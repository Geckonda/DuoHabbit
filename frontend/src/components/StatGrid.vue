<!-- components/StatGrid.vue -->
<script setup>
defineProps({
  // [{ value, label }]
  stats: { type: Array, required: true }
})
</script>

<template>
  <div class="stat-grid">
    <div v-for="(stat, i) in stats" :key="i" class="stat-card">
      <span class="stat-value">{{ stat.value }}</span>
      <span class="stat-label">{{ stat.label }}</span>
    </div>
  </div>
</template>

<style scoped>
.stat-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-3);
}

.stat-card {
  background: var(--surface-card);
  border-radius: var(--radius-lg);
  padding: var(--space-4) var(--space-3);
  text-align: center;
  box-shadow: var(--shadow-sm);
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  display: block;
  margin-bottom: var(--space-1);
}

.stat-label {
  font-size: 12px;
  color: var(--text-tertiary);
}
</style>
