<template>
  <router-view />
</template>

<script setup>
// 使用 Vue Router 来管理页面
</script>

<style>
/* 全局样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  background-color: #ffffff;
}

#app {
  font-family: 'JetBrains Mono', 'Space Grotesk', 'Noto Sans SC', monospace;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #000000;
  /* transparente para revelar o canvas .bg-network atras */
  background-color: transparent;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
}

::-webkit-scrollbar-thumb {
  background: #000000;
}

::-webkit-scrollbar-thumb:hover {
  background: #333333;
}

/* 全局按钮样式 */
button {
  font-family: inherit;
}

/* ============================================================
   Brand mark MIROFISH.BY EMIDGROUP_ — global em qualquer view
   Aplicado tanto em .brand (views internas) quanto .nav-brand
   ============================================================ */
.brand,
.nav-brand {
  display: inline-flex;
  align-items: baseline;
}

.brand .brand-dot,
.nav-brand .brand-dot {
  color: #FF4500;
  font-weight: 900;
  font-size: 1.4em;
  line-height: 1;
  margin-left: 1px;
}

.brand .brand-by,
.nav-brand .brand-by {
  font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace;
  font-weight: 600;
  font-size: 0.6em;
  letter-spacing: 1.2px;
  margin-left: 8px;
  opacity: 0.85;
}

.brand .brand-cursor,
.nav-brand .brand-cursor {
  color: #FF4500;
  font-family: 'JetBrains Mono', 'SF Mono', Menlo, monospace;
  font-weight: 800;
  margin-left: 6px;
  animation: globalBrandBlink 1s step-end infinite;
}

@keyframes globalBrandBlink {
  50% { opacity: 0; }
}
</style>
