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

export const lcmLiveActions = {
    async start(getSreamdata: () => any[]) {
        return new Promise((resolve, reject) => {

            try {
                const userId = crypto.randomUUID();
                const websocketURL = `${window.location.protocol === "https:" ? "wss" : "ws"
                    }:${window.location.host}/api/ws/${userId}`;

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
                            const streamData = getSreamdata();
                            const params = streamData[0];
                            const blob = streamData[1];

                            const jsonString = JSON.stringify({ status: "next_frame", params: params });
                            const jsonBytes = new TextEncoder().encode(jsonString);
                            const jsonLen = jsonBytes.length;

                            if (blob) {
                                blob.arrayBuffer().then((imageBuffer: ArrayBuffer) => {
                                    const totalLen = 4 + jsonLen + imageBuffer.byteLength;
                                    const buffer = new Uint8Array(totalLen);
                                    const view = new DataView(buffer.buffer);
                                    view.setUint32(0, jsonLen, false); // Big Endian
                                    buffer.set(jsonBytes, 4);
                                    buffer.set(new Uint8Array(imageBuffer), 4 + jsonLen);
                                    websocket?.send(buffer);
                                });
                            } else {
                                const totalLen = 4 + jsonLen;
                                const buffer = new Uint8Array(totalLen);
                                const view = new DataView(buffer.buffer);
                                view.setUint32(0, jsonLen, false); // Big Endian
                                buffer.set(jsonBytes, 4);
                                websocket?.send(buffer);
                            }
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
    send(data: Blob | { [key: string]: any }) {
        if (websocket && websocket.readyState === WebSocket.OPEN) {
            if (data instanceof Blob) {
                websocket.send(data);
            } else {
                websocket.send(JSON.stringify(data));
            }
        } else {
            console.log("WebSocket not connected");
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

