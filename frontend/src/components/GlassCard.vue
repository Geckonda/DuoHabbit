<!-- components/GlassCard.vue -->
<script setup>
defineProps({
  title: { type: String, default: '' },
  icon: { type: String, default: '' }
})
</script>

<template>
  <div class="glass-card">
    <h3 v-if="title" class="glass-card-title">
      <span v-if="icon" class="glass-card-icon">{{ icon }}</span>
      {{ title }}
    </h3>
    <slot></slot>
  </div>
</template>

<style scoped>
.glass-card {
  background: var(--surface-card);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  box-shadow: var(--shadow-sm);
}

.glass-card + .glass-card {
  margin-top: var(--space-4);
}

.glass-card-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--space-4);
}

.glass-card-icon {
  font-size: 18px;
}
</style>
