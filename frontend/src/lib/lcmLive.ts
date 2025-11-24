import { writable } from 'svelte/store';


export enum LCMLiveStatus {
    CONNECTED = "connected",
    DISCONNECTED = "disconnected",
    WAIT = "wait",
    SEND_FRAME = "send_frame",
    TIMEOUT = "timeout",
}

const initStatus: LCMLiveStatus = LCMLiveStatus.DISCONNECTED;

export const lcmLiveStatus = writable<LCMLiveStatus>(initStatus);
export const streamId = writable<string | null>(null);
export const userIdStore = writable<string | null>(null);

let websocket: WebSocket | null = null;

type StreamPayload = { params: Record<string, any>; blob?: Blob | null };

function normalizePayload(raw: StreamPayload | any[]): StreamPayload {
    if (Array.isArray(raw)) {
        const [params, blob] = raw;
        return {
            params: (params ?? {}) as Record<string, any>,
            blob: (blob ?? null) as Blob | null,
        };
    }
    if (raw && typeof raw === "object" && "params" in raw) {
        return {
            params: (raw as StreamPayload).params ?? {},
            blob: (raw as StreamPayload).blob ?? null,
        };
    }
    return { params: {}, blob: null };
}

export const lcmLiveActions = {
    async start(getStreamPayload: () => StreamPayload | any[]) {
        return new Promise((resolve, reject) => {

            try {
                       const userId = crypto.randomUUID();
                       // RESTful 规范接口：/api/realtime/sessions/{session_id}/ws
                       const websocketURL = `${window.location.protocol === "https:" ? "wss" : "ws"
                           }:${window.location.host}/api/realtime/sessions/${userId}/ws`;

                websocket = new WebSocket(websocketURL);
                websocket.onopen = () => {
                    console.log("Connected to websocket");
                };
                websocket.onclose = () => {
                    lcmLiveStatus.set(LCMLiveStatus.DISCONNECTED);
                    userIdStore.set(null);
                    streamId.set(null);
                    console.log("Disconnected from websocket");
                };
                websocket.onerror = (err) => {
                    console.error(err);
                };
                websocket.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    switch (data.status) {
                        case "connected":
                            lcmLiveStatus.set(LCMLiveStatus.CONNECTED);
                            streamId.set(userId);
                            userIdStore.set(userId);
                            resolve({ status: "connected", userId });
                            break;
                        case "send_frame":
                            lcmLiveStatus.set(LCMLiveStatus.SEND_FRAME);
                            lcmLiveActions.sendNextFrame(getStreamPayload);
                            break;
                        case "wait":
                            lcmLiveStatus.set(LCMLiveStatus.WAIT);
                            break;
                        case "timeout":
                            console.log("timeout");
                            lcmLiveStatus.set(LCMLiveStatus.TIMEOUT);
                            streamId.set(null);
                            userIdStore.set(null);
                            reject(new Error("timeout"));
                            break;
                        case "error":
                            console.log(data.message);
                            lcmLiveStatus.set(LCMLiveStatus.DISCONNECTED);
                            streamId.set(null);
                            userIdStore.set(null);
                            reject(new Error(data.message));
                            break;
                    }
                };

            } catch (err) {
                console.error(err);
                lcmLiveStatus.set(LCMLiveStatus.DISCONNECTED);
                streamId.set(null);
                userIdStore.set(null);
                reject(err);
            }
        });
    },
    sendJSON(payload: Record<string, any>) {
        if (!websocket || websocket.readyState !== WebSocket.OPEN) {
            console.log("WebSocket not connected");
            return;
        }
        websocket.send(JSON.stringify(payload));
    },
    async sendBinaryFrame(params: Record<string, any>, blob?: Blob | null) {
        if (!websocket || websocket.readyState !== WebSocket.OPEN) {
            console.log("WebSocket not connected");
            return;
        }
        const payload = { status: "next_frame", params };
        const json = new TextEncoder().encode(JSON.stringify(payload));
        const jsonLength = json.length;

        let imageBuffer: ArrayBuffer | null = null;
        if (blob) {
            try {
                imageBuffer = await blob.arrayBuffer();
            } catch (err) {
                console.error("Failed to read blob", err);
            }
        }

        const totalLength = 4 + jsonLength + (imageBuffer ? imageBuffer.byteLength : 0);
        const buffer = new Uint8Array(totalLength);
        const view = new DataView(buffer.buffer);
        view.setUint32(0, jsonLength, false);
        buffer.set(json, 4);
        if (imageBuffer) {
            buffer.set(new Uint8Array(imageBuffer), 4 + jsonLength);
        }
        websocket.send(buffer);
    },
    async sendNextFrame(getStreamPayload: () => StreamPayload | any[]) {
        try {
            const normalized = normalizePayload(getStreamPayload());
            await lcmLiveActions.sendBinaryFrame(normalized.params, normalized.blob ?? undefined);
        } catch (err) {
            console.error("Failed to send next frame", err);
        }
    },
    async stop() {
        lcmLiveStatus.set(LCMLiveStatus.DISCONNECTED);
        if (websocket) {
            websocket.close();
        }
        websocket = null;
        streamId.set(null);
        userIdStore.set(null);
    },
};

