<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="500px"
    :close-on-click-modal="false"
    @closed="handleClosed"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
      <el-form-item label="反馈类型" prop="feedback_type">
        <el-radio-group v-model="form.feedback_type">
          <el-radio value="suggestion">建议改进</el-radio>
          <el-radio value="issue">问题反馈</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="反馈内容" prop="content">
        <el-input
          v-model="form.content"
          type="textarea"
          :rows="5"
          :placeholder="contentPlaceholder"
          maxlength="1000"
          show-word-limit
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">
        提交反馈
      </el-button>
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
