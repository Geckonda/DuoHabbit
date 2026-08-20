<!-- components/HabitPicker.vue -->
<script setup>
defineProps({
  habits: { type: Array, required: true },
  modelValue: { type: Number, default: null }
})

const emit = defineEmits(['update:modelValue', 'pick'])

const typeIcons = {
  daily: '📅',
  weekdays: '💼',
  weekly: '📆',
  monthly: '📊'
}

const pick = (habit) => {
  emit('update:modelValue', habit.id)
  emit('pick', { title: habit.title, description: habit.description || '' })
}
</script>

<template>
  <div class="habit-picker">
    <div class="habit-picker-scroll">
      <button
        v-for="habit in habits"
        :key="habit.id"
        type="button"
        class="habit-chip"
        :class="{ active: modelValue === habit.id }"
        @click="pick(habit)"
      >
        <span class="chip-icon">{{ typeIcons[habit.habit_type] || '📝' }}</span>
        <span class="chip-label">{{ habit.title }}</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.habit-picker-scroll {
  display: flex;
  gap: var(--space-2);
  overflow-x: auto;
  padding-bottom: var(--space-1);
  -webkit-overflow-scrolling: touch;
}

.habit-chip {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  background: var(--surface-card);
  border: 1.5px solid transparent;
  border-radius: var(--radius-pill);
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  box-shadow: var(--shadow-sm);
}

.habit-chip.active {
  border-color: var(--color-accent);
  background: rgba(139, 92, 246, 0.1);
  color: var(--color-accent);
}

.chip-icon {
  font-size: 16px;
}
</style>
