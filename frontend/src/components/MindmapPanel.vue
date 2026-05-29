<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'
import { Network } from 'lucide-vue-next'
import { Transformer } from 'markmap-lib'
import { Markmap } from 'markmap-view'
import { api } from '../api'
import { useStudyStore } from '../stores/study'

const store = useStudyStore()
const topic = ref('计算机网络考试重点')
const markdown = ref('# 计算机网络考试重点\n- 上传资料后可生成导图')
const svg = ref<SVGSVGElement | null>(null)
const transformer = new Transformer()
let markmap: Markmap | null = null

function render() {
  if (!svg.value) return
  const { root } = transformer.transform(markdown.value)
  if (!markmap) {
    markmap = Markmap.create(svg.value, {}, root)
  } else {
    markmap.setData(root)
    markmap.fit()
  }
}

async function generate() {
  markdown.value = (await api.generate('/mindmaps', topic.value, store.selectedCourseId)).content
  await nextTick()
  render()
}

onMounted(render)
</script>

<template>
  <section class="panel mindmap-panel">
    <header class="panel-header">
      <Network :size="20" />
      <h2>思维导图</h2>
    </header>
    <div class="inline-form">
      <input v-model="topic" placeholder="导图主题" />
      <button @click="generate">
        <Network :size="18" />
        <span>生成</span>
      </button>
    </div>
    <svg ref="svg" class="mindmap-canvas"></svg>
  </section>
</template>
