<template>
  <el-dialog
    v-model="visible"
    title="推荐新工具"
    width="520px"
    :close-on-click-modal="false"
    class="want-tool-dialog"
    @closed="handleClosed"
  >
    <!-- 顶部提示 -->
    <div class="dialog-tip">
      <span class="tip-icon">✨</span>
      <span class="tip-text">推荐一个AI工具，让更多人发现它的价值</span>
    </div>

    <el-form ref="formRef" :model="form" :rules="rules" label-position="top" class="want-form">
      <el-form-item label="工具名称" prop="tool_name">
        <el-input
          v-model="form.tool_name"
          placeholder="例如：Claude、Midjourney、Cursor..."
          maxlength="100"
          show-word-limit
          class="form-input"
        >
          <template #prefix>
            <span class="input-icon">🔧</span>
          </template>
        </el-input>
      </el-form-item>

      <el-form-item label="工具链接" prop="tool_url">
        <el-input
          v-model="form.tool_url"
          placeholder="https://example.com（选填）"
          maxlength="500"
          class="form-input"
        >
          <template #prefix>
            <span class="input-icon">🔗</span>
          </template>
        </el-input>
      </el-form-item>

      <el-form-item label="推荐理由" prop="content">
        <el-input
          v-model="form.content"
          type="textarea"
          :rows="4"
          placeholder="说说这个工具的亮点，能解决什么问题..."
          maxlength="500"
          show-word-limit
          class="content-input"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="visible = false" class="cancel-btn">取消</el-button>
        <el-button type="primary" :loading="loading" @click="handleSubmit" class="submit-btn">
          <span v-if="!loading">提交推荐</span>
          <span v-else>提交中...</span>
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { feedbackApi } from '@/api'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

const visible = ref(false)
const loading = ref(false)
const formRef = ref(null)

const form = ref({
  tool_name: '',
  tool_url: '',
  content: ''
})

const rules = {
  tool_name: [
    { required: true, message: '请输入工具名称', trigger: 'blur' },
    { min: 2, max: 100, message: '工具名称需要2-100个字符', trigger: 'blur' }
  ],
  content: [
    { max: 500, message: '推荐理由不能超过500字', trigger: 'blur' }
  ]
}

watch(() => props.modelValue, (val) => {
  visible.value = val
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

function handleClosed() {
  form.value = {
    tool_name: '',
    tool_url: '',
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
      feedback_type: 'want',
      tool_name: form.value.tool_name,
      tool_url: form.value.tool_url || null,
      content: form.value.content || null
    })
    ElMessage.success('提交成功，感谢您的推荐！')
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
/* 顶部提示 */
.dialog-tip {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 18px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
  border-radius: 12px;
  margin-bottom: 24px;
}

.tip-icon {
  font-size: 20px;
}

.tip-text {
  font-size: 14px;
  color: var(--text-secondary, #64748b);
}

/* 表单样式 */
.want-form :deep(.el-form-item__label) {
  font-weight: 600;
  color: var(--text-primary, #1e293b);
}

.form-input :deep(.el-input__wrapper) {
  border-radius: 12px;
  padding: 4px 16px;
}

.form-input :deep(.el-input__wrapper:focus-within) {
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15);
}

.input-icon {
  font-size: 16px;
  margin-right: 4px;
}

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
.want-tool-dialog .el-dialog {
  border-radius: 20px;
  overflow: hidden;
}

.want-tool-dialog .el-dialog__header {
  padding: 20px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  margin: 0;
}

.want-tool-dialog .el-dialog__title {
  color: #fff;
  font-weight: 600;
  font-size: 18px;
}

.want-tool-dialog .el-dialog__headerbtn .el-dialog__close {
  color: #fff;
}

.want-tool-dialog .el-dialog__body {
  padding: 24px;
}

.want-tool-dialog .el-dialog__footer {
  padding: 16px 24px 24px;
}
</style>
