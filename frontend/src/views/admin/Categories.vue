<template>
  <div class="categories-page">
    <!-- 操作栏 -->
    <div class="toolbar">
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>
        添加分类
      </el-button>
    </div>

    <!-- 分类列表 -->
    <el-table :data="tableData" v-loading="loading" stripe row-key="id">
      <el-table-column prop="name" label="分类名称" width="200">
        <template #default="{ row }">
          <span v-if="row.parent_id" class="indent">└ </span>
          <span class="cat-icon" :style="{ background: row.color || '#667eea' }">
            {{ row.name.charAt(0) }}
          </span>
          {{ row.name }}
        </template>
      </el-table-column>
      <el-table-column prop="color" label="主题色" width="120">
        <template #default="{ row }">
          <div class="color-preview" :style="{ background: row.color || '#667eea' }"></div>
          <span>{{ row.color || '#667eea' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="sort_order" label="排序" width="80" />
      <el-table-column label="工具数" width="80">
        <template #default="{ row }">
          {{ row.tool_count || 0 }}
        </template>
      </el-table-column>
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
            {{ row.is_active ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" text size="small" @click="handleEdit(row)">
            编辑
          </el-button>
          <el-popconfirm
            title="确定删除该分类？"
            @confirm="handleDelete(row.id)"
          >
            <template #reference>
              <el-button type="danger" text size="small">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- 编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑分类' : '添加分类'"
      width="450px"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="80px"
      >
        <el-form-item label="名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入分类名称" />
        </el-form-item>
        <el-form-item label="父分类" prop="parent_id">
          <el-select
            v-model="formData.parent_id"
            placeholder="无（作为一级分类）"
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="cat in parentOptions"
              :key="cat.id"
              :label="cat.name"
              :value="cat.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="主题色" prop="color">
          <el-color-picker v-model="formData.color" />
          <span class="color-tip">{{ formData.color || '默认 #667eea' }}</span>
        </el-form-item>
        <el-form-item label="图标URL" prop="icon_url">
          <el-input v-model="formData.icon_url" placeholder="可选" />
        </el-form-item>
        <el-form-item label="排序" prop="sort_order">
          <el-input-number v-model="formData.sort_order" :min="0" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="formData.is_active" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { adminApi } from '@/api'

const loading = ref(false)
const submitting = ref(false)
const categories = ref([])

const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const formRef = ref(null)

const formData = reactive({
  name: '',
  parent_id: null,
  color: '#667eea',
  icon_url: '',
  sort_order: 0,
  is_active: true
})

const formRules = {
  name: [{ required: true, message: '请输入分类名称', trigger: 'blur' }]
}

// 构建表格数据（按层级排序）
const tableData = computed(() => {
  const result = []
  const parents = categories.value.filter(c => !c.parent_id)

  for (const parent of parents) {
    result.push(parent)
    const children = categories.value.filter(c => c.parent_id === parent.id)
    for (const child of children) {
      result.push(child)
    }
  }

  return result
})

// 父分类选项（只能选择一级分类）
const parentOptions = computed(() => {
  const opts = categories.value.filter(c => !c.parent_id)
  // 编辑时排除自己
  if (isEdit.value && editId.value) {
    return opts.filter(c => c.id !== editId.value)
  }
  return opts
})

onMounted(() => {
  loadCategories()
})

async function loadCategories() {
  try {
    loading.value = true
    categories.value = await adminApi.getCategories()
  } catch (error) {
    console.error('加载分类失败:', error)
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

function handleAdd() {
  isEdit.value = false
  editId.value = null
  resetForm()
  dialogVisible.value = true
}

function handleEdit(row) {
  isEdit.value = true
  editId.value = row.id
  Object.assign(formData, {
    name: row.name,
    parent_id: row.parent_id,
    color: row.color || '#667eea',
    icon_url: row.icon_url || '',
    sort_order: row.sort_order || 0,
    is_active: row.is_active
  })
  dialogVisible.value = true
}

async function handleSubmit() {
  try {
    await formRef.value.validate()
    submitting.value = true

    const data = { ...formData }
    // 如果颜色是默认值则置空
    if (data.color === '#667eea') data.color = null

    if (isEdit.value) {
      await adminApi.updateCategory(editId.value, data)
      ElMessage.success('更新成功')
    } else {
      await adminApi.createCategory(data)
      ElMessage.success('创建成功')
    }

    dialogVisible.value = false
    loadCategories()
  } catch (error) {
    if (error !== false) {
      console.error('提交失败:', error)
      ElMessage.error(error.response?.data?.detail || '操作失败')
    }
  } finally {
    submitting.value = false
  }
}

async function handleDelete(id) {
  try {
    await adminApi.deleteCategory(id)
    ElMessage.success('删除成功')
    loadCategories()
  } catch (error) {
    console.error('删除失败:', error)
    ElMessage.error(error.response?.data?.detail || '删除失败')
  }
}

function resetForm() {
  Object.assign(formData, {
    name: '',
    parent_id: null,
    color: '#667eea',
    icon_url: '',
    sort_order: 0,
    is_active: true
  })
}
</script>

<style scoped>
.categories-page {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
}

.toolbar {
  margin-bottom: 16px;
}

.indent {
  color: #c0c4cc;
  margin-right: 4px;
}

.cat-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  margin-right: 8px;
}

.color-preview {
  display: inline-block;
  width: 16px;
  height: 16px;
  border-radius: 4px;
  margin-right: 8px;
  vertical-align: middle;
}

.color-tip {
  margin-left: 12px;
  color: #909399;
  font-size: 13px;
}
</style>
