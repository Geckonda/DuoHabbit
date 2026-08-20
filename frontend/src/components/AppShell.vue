<!-- components/AppShell.vue -->
<script setup>
import { useRoute } from 'vue-router'
import BottomTabBar from './BottomTabBar.vue'

const route = useRoute()
</script>

<template>
  <router-view v-slot="{ Component }">
    <transition name="fade" mode="out-in">
      <component :is="Component" />
    </transition>
  </router-view>

  <BottomTabBar v-if="route.meta.tabBar" />
</template>
