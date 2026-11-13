<template>
  <div>
    <el-card>
      <template #header>
        <div style="font-size: 16px; font-weight: bold">
          <span>AI智能助手</span>
        </div>
      </template>
      <div
        ref="listRef"
        style="
          height: 480px;
          overflow-y: auto;
          padding: 8px 4px;
          background-color: #fafafa;
          border-radius: 6px;
        "
      >
        <div
          v-for="(item, index) in messages"
          :key="index"
          :style="{
            display: 'flex',
            justifyContent: item.role === 'user' ? 'flex-end' : 'flex-start',
            marginBottom: '12px'
          }"
        >
          <div
            :style="{
              maxWidth: '70%',
              padding: '10px 12px',
              borderRadius: '8px',
              backgroundColor: item.role === 'user' ? '#409eff' : '#fff',
              color: item.role === 'user' ? '#fff' : '#333',
              lineHeight: '1.6',
              boxShadow: '0 1px 2px rgba(0,0,0,0.06)'
            }"
          >
            <!-- 当前进行中的一句话-->
            <div
              v-if="item.role === 'assistant' && item.status"
              style="margin-bottom: 6px; font-size: 12px; color: #909399"
            >
              {{ item.status }}
            </div>
            <!--本轮已发生的过程列表，只展示不传回给后端-->
            <div
              v-if="item.role === 'assistant' && item.steps?.length"
              style="margin-bottom: 8px; font-size: 12px; color: #909399; line-height: 1.5"
            >
              <div v-for="(step, i) in item.steps" :key="i">.{{ step }}</div>
            </div>
            <div v-if="item.content" v-html="parseMarkdown(item.content)"></div>
          </div>
        </div>
      </div>
      <!--输入框-->
      <div style="margin-top: 12px; display: flex; gap: 8px; align-items: flex-end">
        <el-input
          v-model="input"
          type="textarea"
          :rows="2"
          placeholder="问问实验室怎么预约、开放时间..."
          @keydown.enter.exact.prevent="handleSend"
          @keydown.enter.shift.stop
        >
        </el-input>
        <el-button type="primary" @click="handleSend">发送</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { chatStreamApi } from '@/api/ai'
import { nextTick, onMounted, reactive, ref } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { ElMessage } from 'element-plus'

const messages = ref([
  {
    role: 'assistant',
    content:
      '您好，我是实验室助手。你可以向我查询实验室或设备信息及预约方式，也可以给我指令让我预约。'
  }
])
const input = ref('')
const loading = ref(false)
const listRef = ref()
const scrollToBottom = () => {
  nextTick(() => {
    const elem = listRef.value
    if (elem) elem.scrollTop = elem.scrollHeight
  })
}
const handleSend = async () => {
  const text = input.value.trim()
  if (!text || loading.value) return
  messages.value.push({ role: 'user', content: text })
  input.value = ''
  loading.value = true
  scrollToBottom()
  // 必须用reactive:普通对象push后再改字段，视图可能不更新
  const assistant = reactive({
    role: 'assistant',
    content: '',
    status: '正在思考...', //当前状态文案
    steps: [] //过程流水，不进下次hsitory
  })
  messages.value.push(assistant)
  const history = messages.value
    .filter((item) => item.role === 'user' || item.role === 'assistant')
    .slice(0, -1) //去掉刚插入的空助手,前端提前预插入了一条空的 `assistant` 消息占位
    //只保留role/content;status、steps丢掉
    .map(({ role, content }) => ({ role, content }))
  try {
    await chatStreamApi({ messages: history }, (evt) => {
      if (evt.type === 'status') {
        assistant.status = evt.message || '正在思考…'
      } else if (evt.type === 'tool_start') {
        const label = evt.label || evt.name || '工具'
        assistant.status = `正在${label}…`
        assistant.steps.push(`开始：${label}`)
      } else if (evt.type === 'tool_end') {
        const label = evt.label || evt.name || '工具'
        assistant.status = `${label}完成`
        assistant.steps.push(`完成：${label}`)
        if (evt.preview) {
          assistant.steps.push(`输出结果：${evt.preview}`)
        }
      } else if (evt.type === 'token') {
        assistant.content += evt.content || '' //打字机：追加，不是覆盖
        assistant.status = '' //开始出字后清掉 [正在…]，避免叠在一起
      } else if (evt.type === 'error') {
        assistant.status = ''
        if (!assistant.content) {
          assistant.content = evt.message || '请求失败'
        }
        ElMessage.error(err.message || '请求失败')
      }
      scrollToBottom()
    })
  } catch (err) {
    assistant.status = ''
    if (!assistant.content) {
      assistant.content = err.message || '网络异常'
    }
    ElMessage.error(err.message || '网络异常')
  } finally {
    loading.value = false
    assistant.status = ''
    scrollToBottom()
  }
}

const parseMarkdown = (text) => {
  if (!text) return ''
  marked.setOptions({ breaks: true }) //将\n转换成<br>
  const rawHtml = marked.parse(text)
  return DOMPurify.sanitize(rawHtml)
}
</script>
