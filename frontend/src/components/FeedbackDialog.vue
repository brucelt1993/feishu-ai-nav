<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="520px"
    :close-on-click-modal="false"
    class="feedback-dialog"
    @closed="handleClosed"
  >
    <!-- 工具信息提示 -->
    <div v-if="tool" class="tool-info-banner">
      <div class="tool-icon" :style="{ background: tool.category_color || '#667eea' }">
        <img v-if="tool.icon_url" :src="tool.icon_url" :alt="tool.name" />
        <span v-else>{{ tool.name.charAt(0) }}</span>
      </div>
      <div class="tool-details">
        <div class="tool-name">{{ tool.name }}</div>
        <div class="tool-desc">{{ tool.description }}</div>
      </div>
    </div>

    <el-form ref="formRef" :model="form" :rules="rules" label-position="top" class="feedback-form">
      <el-form-item label="反馈类型" prop="feedback_type">
        <div class="type-selector">
          <button
            type="button"
            class="type-btn"
            :class="{ active: form.feedback_type === 'suggestion' }"
            @click="form.feedback_type = 'suggestion'"
          >
            <span class="type-icon">💡</span>
            <span class="type-label">建议改进</span>
          </button>
          <button
            type="button"
            class="type-btn"
            :class="{ active: form.feedback_type === 'issue' }"
            @click="form.feedback_type = 'issue'"
          >
            <span class="type-icon">⚠️</span>
            <span class="type-label">问题反馈</span>
          </button>
        </div>
      </el-form-item>

      <el-form-item label="反馈内容" prop="content">
        <el-input
          v-model="form.content"
          type="textarea"
          :rows="5"
          :placeholder="contentPlaceholder"
          maxlength="1000"
          show-word-limit
          class="content-input"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="visible = false" class="cancel-btn">取消</el-button>
        <el-button type="primary" :loading="loading" @click="handleSubmit" class="submit-btn">
          <span v-if="!loading">提交反馈</span>
          <span v-else>提交中...</span>
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { feedbackApi } from '@/api'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  tool: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

const visible = ref(false)
const loading = ref(false)
const formRef = ref(null)

const form = ref({
  feedback_type: 'suggestion',
  content: ''
})

const rules = {
  feedback_type: [
    { required: true, message: '请选择反馈类型', trigger: 'change' }
  ],
  content: [
    { required: true, message: '请输入反馈内容', trigger: 'blur' },
    { min: 5, max: 1000, message: '反馈内容需要5-1000个字符', trigger: 'blur' }
  ]
}

const dialogTitle = computed(() => {
  if (props.tool) {
    return `反馈 - ${props.tool.name}`
  }
  return '提交反馈'
})

const contentPlaceholder = computed(() => {
  if (form.value.feedback_type === 'issue') {
    return '请描述您遇到的问题，比如链接无法访问、信息过时等...'
  }
  return '请描述您的建议，比如希望增加什么功能、改进哪些方面...'
})

watch(() => props.modelValue, (val) => {
  visible.value = val
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

function handleClosed() {
  form.value = {
    feedback_type: 'suggestion',
    content: ''
  }
  formRef.value?.resetFields()
}

async function handleSubmit() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  loading.value = true
  try {
    await feedbackApi.create({
      feedback_type: form.value.feedback_type,
      tool_id: props.tool?.id || null,
      content: form.value.content
    })
    ElMessage.success('反馈提交成功，感谢您的反馈！')
    visible.value = false
    emit('success')
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error('提交失败，请稍后重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* 工具信息横幅 */
.tool-info-banner {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.08), rgba(118, 75, 162, 0.08));
  border-radius: 12px;
  margin-bottom: 24px;
}

.tool-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #fff;
  font-size: 18px;
  font-weight: 700;
}

.tool-icon img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 12px;
}

.tool-details {
  flex: 1;
  min-width: 0;
}

.tool-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary, #1e293b);
  margin-bottom: 4px;
}

.tool-desc {
  font-size: 13px;
  color: var(--text-secondary, #64748b);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 反馈表单 */
.feedback-form :deep(.el-form-item__label) {
  font-weight: 600;
  color: var(--text-primary, #1e293b);
}

/* 类型选择器 */
.type-selector {
  display: flex;
  gap: 12px;
  width: 100%;
}

.type-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px;
  border: 2px solid var(--border-color, #e2e8f0);
  border-radius: 12px;
  background: var(--bg-secondary, #ffffff);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.type-btn:hover {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.05);
}

.type-btn.active {
  border-color: #667eea;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
}

.type-icon {
  font-size: 24px;
}

.type-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary, #1e293b);
}

/* 内容输入框 */
.content-input :deep(.el-textarea__inner) {
  border-radius: 12px;
  padding: 14px 16px;
  font-size: 14px;
  line-height: 1.6;
  resize: none;
}

.content-input :deep(.el-textarea__inner:focus) {
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15);
}

/* 弹窗底部 */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.cancel-btn {
  border-radius: 10px;
  padding: 10px 24px;
}

.submit-btn {
  border-radius: 10px;
  padding: 10px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.submit-btn:hover {
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
}
</style>

<style>
/* 全局样式覆盖弹窗 */
.feedback-dialog .el-dialog {
  border-radius: 20px;
  overflow: hidden;
}

.feedback-dialog .el-dialog__header {
  padding: 20px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  margin: 0;
}

.feedback-dialog .el-dialog__title {
  color: #fff;
  font-weight: 600;
  font-size: 18px;
}

.feedback-dialog .el-dialog__headerbtn .el-dialog__close {
  color: #fff;
}

.feedback-dialog .el-dialog__body {
  padding: 24px;
}

.feedback-dialog .el-dialog__footer {
  padding: 16px 24px 24px;
}
</style>
