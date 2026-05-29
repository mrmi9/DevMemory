<script setup lang="ts">
import { nextTick, onMounted, ref, watch } from 'vue'
import { Network, RefreshCw, Trash2 } from 'lucide-vue-next'
import AppModal from './AppModal.vue'
import { api, type Mindmap } from '../api'
import { useStudyStore } from '../stores/study'

const store = useStudyStore()
const topic = ref('计算机网络考试重点')
const markdown = ref('# 计算机网络考试重点\n- 上传资料后可生成导图')
const mindmaps = ref<Mindmap[]>([])
const selectedMindmapId = ref('')
const busy = ref('')
const error = ref('')
const svg = ref<SVGSVGElement | null>(null)
const mindmapPendingDelete = ref<Mindmap | null>(null)
type MarkmapInstance = { setData: (root: unknown) => void; fit: () => void }

let transformer: { transform: (content: string) => { root: unknown } } | null = null
let markmap: MarkmapInstance | null = null
let createMarkmap: ((target: SVGSVGElement, root: unknown) => MarkmapInstance) | null = null

async function loadMarkmap() {
  if (!transformer || !createMarkmap) {
    const [{ Transformer }, { Markmap }] = await Promise.all([import('markmap-lib'), import('markmap-view')])
    transformer = new Transformer()
    createMarkmap = (target, root) => Markmap.create(target, {}, root as never) as MarkmapInstance
  }
  return { transformer, createMarkmap }
}

async function render() {
  if (!svg.value) return
  const { transformer, createMarkmap } = await loadMarkmap()
  const { root } = transformer.transform(markdown.value)
  if (!markmap) {
    markmap = createMarkmap(svg.value, root)
  } else {
    markmap.setData(root)
    markmap.fit()
  }
}

async function loadMindmaps() {
  error.value = ''
  if (!store.selectedCourseId) {
    mindmaps.value = []
    selectedMindmapId.value = ''
    markdown.value = '# 暂无课程\n- 选择课程后生成思维导图'
    await nextTick()
    await render()
    return
  }
  try {
    mindmaps.value = await api.listMindmaps(store.selectedCourseId)
    if (!mindmaps.value.some((item) => item.id === selectedMindmapId.value)) {
      selectedMindmapId.value = mindmaps.value[0]?.id ?? ''
    }
    syncSelectedMindmap()
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  }
  await nextTick()
  await render()
}

function syncSelectedMindmap() {
  const selected = mindmaps.value.find((item) => item.id === selectedMindmapId.value)
  if (selected) {
    markdown.value = selected.markdown
  } else if (!mindmaps.value.length) {
    markdown.value = '# 暂无思维导图\n- 输入主题后生成第一张导图'
  }
}

async function selectMindmap(mindmap: Mindmap) {
  selectedMindmapId.value = mindmap.id
  syncSelectedMindmap()
  await nextTick()
  await render()
}

async function generate() {
  busy.value = 'generate'
  error.value = ''
  try {
    const response = await api.generateMindmap(topic.value, store.selectedCourseId)
    markdown.value = response.content
    await loadMindmaps()
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
    await nextTick()
    await render()
  } finally {
    busy.value = ''
  }
}

function deleteSelectedMindmap() {
  const selected = mindmaps.value.find((item) => item.id === selectedMindmapId.value)
  if (!selected) return
  mindmapPendingDelete.value = selected
  error.value = ''
}

async function confirmDeleteSelectedMindmap() {
  if (!mindmapPendingDelete.value) return
  const selected = mindmapPendingDelete.value
  busy.value = 'delete'
  error.value = ''
  try {
    await api.deleteMindmap(selected.id)
    mindmaps.value = mindmaps.value.filter((item) => item.id !== selected.id)
    selectedMindmapId.value = mindmaps.value[0]?.id ?? ''
    syncSelectedMindmap()
    mindmapPendingDelete.value = null
    await nextTick()
    await render()
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  } finally {
    busy.value = ''
  }
}

onMounted(loadMindmaps)
watch(() => store.selectedCourseId, loadMindmaps)
</script>

<template>
  <section class="panel mindmap-panel">
    <header class="panel-header">
      <Network :size="20" />
      <h2>思维导图</h2>
      <button class="icon-button" type="button" title="刷新思维导图" :disabled="!!busy" @click="loadMindmaps">
        <RefreshCw :size="16" />
      </button>
    </header>
    <div class="inline-form">
      <input v-model="topic" placeholder="导图主题" />
      <button @click="generate" :disabled="!!busy || !store.selectedCourseId || !topic.trim()">
        <Network :size="18" />
        <span>{{ busy === 'generate' ? '生成中' : '生成' }}</span>
      </button>
    </div>

    <div class="mindmap-list">
      <button
        v-for="mindmap in mindmaps"
        :key="mindmap.id"
        class="mindmap-list-item"
        :class="{ active: mindmap.id === selectedMindmapId }"
        type="button"
        @click="selectMindmap(mindmap)"
      >
        <strong>{{ mindmap.title }}</strong>
        <small>{{ new Date(mindmap.created_at).toLocaleString() }}</small>
      </button>
      <p v-if="!mindmaps.length" class="muted">当前课程还没有保存的思维导图。</p>
    </div>

    <div class="detail-actions">
      <button
        class="danger-button"
        type="button"
        title="删除思维导图"
        :disabled="!!busy || !selectedMindmapId"
        @click="deleteSelectedMindmap"
      >
        <Trash2 :size="16" />
        <span>{{ busy === 'delete' ? '删除中' : '删除导图' }}</span>
      </button>
    </div>

    <p v-if="error" class="inline-error">{{ error }}</p>
    <svg ref="svg" class="mindmap-canvas"></svg>
    <AppModal
      :open="!!mindmapPendingDelete"
      title="删除思维导图"
      confirm-label="删除导图"
      danger
      :busy="busy === 'delete'"
      :error="error"
      @close="mindmapPendingDelete = null"
      @confirm="confirmDeleteSelectedMindmap"
    >
      <p>确定删除“{{ mindmapPendingDelete?.title }}”吗？该操作无法撤销。</p>
    </AppModal>
  </section>
</template>
