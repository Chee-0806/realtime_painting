<script lang="ts">
  export let variant: 'primary' | 'secondary' | 'success' | 'danger' | 'warning' | 'ghost' = 'primary';
  export let disabled: boolean = false;
  export let classList: string | Record<string, boolean> = '';
  
  $: classes = typeof classList === 'string' 
    ? classList 
    : Object.entries(classList)
        .filter(([_, active]) => active)
        .map(([cls]) => cls)
        .join(' ');
  
  $: buttonClass = `btn-${variant} ${classes}`.trim();
</script>

<button
  class={buttonClass}
  {disabled}
  on:click
  type="button"
>
  <slot />
</button>

