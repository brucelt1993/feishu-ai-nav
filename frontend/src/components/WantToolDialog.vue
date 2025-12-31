<template>
  <el-dialog
    v-model="visible"
    title="我想要这个工具"
    width="500px"
    :close-on-click-modal="false"
    @closed="handleClosed"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
      <el-form-item label="工具名称" prop="tool_name">
        <el-input
          v-model="form.tool_name"
          placeholder="请输入想要的工具名称"
          maxlength="100"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="工具链接" prop="tool_url">
        <el-input
          v-model="form.tool_url"
          placeholder="请输入工具链接（选填）"
          maxlength="500"
        />
      </el-form-item>

      <el-form-item label="推荐理由" prop="content">
        <el-input
          v-model="form.content"
          type="textarea"
          :rows="4"
          placeholder="说说为什么想要这个工具，它能解决什么问题..."
          maxlength="500"
          show-word-limit
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">
        提交
      </el-button>
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
    ElMessage.success('提交成功，感谢您的建议！')
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
