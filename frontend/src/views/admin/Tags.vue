<template>
  <div class="tags-page">
    <!-- 操作栏 -->
    <div class="action-bar">
      <el-button type="primary" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>
        新建标签
      </el-button>
    </div>

    <!-- 标签列表 -->
    <div class="tags-card">
      <el-table :data="tags" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column label="标签名称" min-width="150">
          <template #default="{ row }">
            <el-tag :style="{ background: row.color, borderColor: row.color }" effect="dark">
              {{ row.name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="颜色" width="120">
          <template #default="{ row }">
            <div class="color-cell">
              <span class="color-dot" :style="{ background: row.color }"></span>
              <span>{{ row.color }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="tool_count" label="关联工具数" width="120" align="center" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="showEditDialog(row)">编辑</el-button>
            <el-popconfirm
              title="确定要删除这个标签吗？"
              confirm-button-text="删除"
              cancel-button-text="取消"
              @confirm="handleDelete(row.id)"
            >
              <template #reference>
                <el-button type="danger" link>删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 新建/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑标签' : '新建标签'"
      width="400px"
      @close="resetForm"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="标签名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入标签名称" maxlength="50" />
        </el-form-item>
        <el-form-item label="标签颜色" prop="color">
          <div class="color-picker-row">
            <el-color-picker v-model="form.color" />
            <el-input v-model="form.color" placeholder="#667eea" style="margin-left: 12px;" />
          </div>
          <div class="preset-colors">
            <button
              v-for="color in presetColors"
              :key="color"
              class="preset-color"
              :class="{ active: form.color === color }"
              :style="{ background: color }"
              @click.prevent="form.color = color"
            ></button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ isEdit ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { adminApi } from '@/api'

const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const formRef = ref(null)

const tags = ref([])

const form = reactive({
  name: '',
  color: '#667eea'
})

const rules = {
  name: [{ required: true, message: '请输入标签名称', trigger: 'blur' }],
  color: [{ required: true, message: '请选择颜色', trigger: 'change' }]
}

const presetColors = [
  '#667eea', '#764ba2', '#f56c6c', '#e6a23c', '#67c23a',
  '#409eff', '#909399', '#6366f1', '#ec4899', '#14b8a6'
]

onMounted(() => {
  loadTags()
})

async function loadTags() {
  loading.value = true
  try {
    const res = await adminApi.getTags()
    tags.value = res.items || []
  } catch (error) {
    console.error('加载标签失败:', error)
  } finally {
    loading.value = false
  }
}

function showCreateDialog() {
  isEdit.value = false
  editingId.value = null
  form.name = ''
  form.color = '#667eea'
  dialogVisible.value = true
}

function showEditDialog(tag) {
  isEdit.value = true
  editingId.value = tag.id
  form.name = tag.name
  form.color = tag.color
  dialogVisible.value = true
}

function resetForm() {
  formRef.value?.resetFields()
}

async function handleSubmit() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  submitting.value = true
  try {
    if (isEdit.value) {
      await adminApi.updateTag(editingId.value, form)
      ElMessage.success('更新成功')
    } else {
      await adminApi.createTag(form)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadTags()
  } catch (error) {
    console.error('提交失败:', error)
  } finally {
    submitting.value = false
  }
}

async function handleDelete(id) {
  try {
    await adminApi.deleteTag(id)
    ElMessage.success('删除成功')
    loadTags()
  } catch (error) {
    console.error('删除失败:', error)
  }
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.tags-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.action-bar {
  display: flex;
  justify-content: flex-end;
}

.tags-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
}

.color-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.color-dot {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  flex-shrink: 0;
}

.color-picker-row {
  display: flex;
  align-items: center;
}

.preset-colors {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.preset-color {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
}

.preset-color:hover {
  transform: scale(1.1);
}

.preset-color.active {
  border-color: #303133;
  box-shadow: 0 0 0 2px rgba(0, 0, 0, 0.1);
}
</style>
