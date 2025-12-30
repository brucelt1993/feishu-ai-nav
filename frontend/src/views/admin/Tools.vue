<template>
  <div class="tools-page">
    <!-- 操作栏 -->
    <div class="toolbar">
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>
        添加工具
      </el-button>
      <el-select
        v-model="filterCategoryId"
        placeholder="筛选分类"
        clearable
        style="width: 200px; margin-left: 12px"
        @change="loadTools"
      >
        <el-option-group
          v-for="parent in categoryTree"
          :key="parent.id"
          :label="parent.name"
        >
          <el-option :label="parent.name + '（全部）'" :value="parent.id" />
          <el-option
            v-for="child in parent.children"
            :key="child.id"
            :label="'└ ' + child.name"
            :value="child.id"
          />
        </el-option-group>
      </el-select>
    </div>

    <!-- 工具列表 -->
    <el-table :data="tools" v-loading="loading" stripe>
      <el-table-column type="index" label="#" width="60" />
      <el-table-column label="图标" width="80">
        <template #default="{ row }">
          <el-avatar :src="row.icon_url" :size="40" shape="square">
            {{ row.name?.charAt(0) }}
          </el-avatar>
        </template>
      </el-table-column>
      <el-table-column prop="name" label="名称" width="150" />
      <el-table-column prop="description" label="描述" show-overflow-tooltip />
      <el-table-column label="分类" width="120">
        <template #default="{ row }">
          <el-tag v-if="row.category" size="small" :color="row.category.color" effect="dark">
            {{ row.category.name }}
          </el-tag>
          <span v-else class="no-category">未分类</span>
        </template>
      </el-table-column>
      <el-table-column prop="sort_order" label="排序" width="80" />
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
            title="确定删除该工具？"
            @confirm="handleDelete(row.id)"
          >
            <template #reference>
              <el-button type="danger" text size="small">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="size"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @change="loadTools"
      />
    </div>

    <!-- 编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑工具' : '添加工具'"
      width="500px"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="80px"
      >
        <el-form-item label="名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入工具名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="2"
            placeholder="请输入工具描述"
          />
        </el-form-item>
        <el-form-item label="图标URL" prop="icon_url">
          <el-input v-model="formData.icon_url" placeholder="请输入图标URL" />
        </el-form-item>
        <el-form-item label="跳转链接" prop="target_url">
          <el-input v-model="formData.target_url" placeholder="请输入目标URL" />
        </el-form-item>
        <el-form-item label="分类" prop="category_id">
          <el-cascader
            v-model="categoryPath"
            :options="categoryOptions"
            :props="{ checkStrictly: true, emitPath: false, value: 'id', label: 'name' }"
            placeholder="请选择分类"
            clearable
            style="width: 100%"
          />
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
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { adminApi } from '@/api'

const loading = ref(false)
const submitting = ref(false)
const tools = ref([])
const categories = ref([])
const total = ref(0)
const page = ref(1)
const size = ref(20)
const filterCategoryId = ref(null)

const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const formRef = ref(null)
const categoryPath = ref(null)

const formData = reactive({
  name: '',
  description: '',
  icon_url: '',
  target_url: '',
  category_id: null,
  sort_order: 0,
  is_active: true
})

const formRules = {
  name: [{ required: true, message: '请输入工具名称', trigger: 'blur' }],
  target_url: [{ required: true, message: '请输入跳转链接', trigger: 'blur' }]
}

// 构建分类树（用于筛选）
const categoryTree = computed(() => {
  const parents = categories.value.filter(c => !c.parent_id)
  return parents.map(p => ({
    ...p,
    children: categories.value.filter(c => c.parent_id === p.id)
  }))
})

// 构建级联选项（用于表单）
const categoryOptions = computed(() => {
  return categoryTree.value.map(parent => ({
    id: parent.id,
    name: parent.name,
    children: parent.children.map(child => ({
      id: child.id,
      name: child.name
    }))
  }))
})

// 监听categoryPath变化，同步到formData
watch(categoryPath, (val) => {
  formData.category_id = val
})

onMounted(async () => {
  await loadCategories()
  await loadTools()
})

async function loadCategories() {
  try {
    categories.value = await adminApi.getCategories()
  } catch (error) {
    console.error('加载分类失败:', error)
  }
}

async function loadTools() {
  try {
    loading.value = true
    const res = await adminApi.getTools(page.value, size.value, filterCategoryId.value)
    tools.value = res.items
    total.value = res.total
  } catch (error) {
    console.error('加载工具列表失败:', error)
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
    description: row.description || '',
    icon_url: row.icon_url || '',
    target_url: row.target_url,
    category_id: row.category_id,
    sort_order: row.sort_order || 0,
    is_active: row.is_active
  })
  categoryPath.value = row.category_id
  dialogVisible.value = true
}

async function handleSubmit() {
  try {
    await formRef.value.validate()
    submitting.value = true

    if (isEdit.value) {
      await adminApi.updateTool(editId.value, formData)
      ElMessage.success('更新成功')
    } else {
      await adminApi.createTool(formData)
      ElMessage.success('创建成功')
    }

    dialogVisible.value = false
    loadTools()
  } catch (error) {
    if (error !== false) {
      console.error('提交失败:', error)
      ElMessage.error('操作失败')
    }
  } finally {
    submitting.value = false
  }
}

async function handleDelete(id) {
  try {
    await adminApi.deleteTool(id)
    ElMessage.success('删除成功')
    loadTools()
  } catch (error) {
    console.error('删除失败:', error)
    ElMessage.error('删除失败')
  }
}

function resetForm() {
  Object.assign(formData, {
    name: '',
    description: '',
    icon_url: '',
    target_url: '',
    category_id: null,
    sort_order: 0,
    is_active: true
  })
  categoryPath.value = null
}
</script>

<style scoped>
.tools-page {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
}

.toolbar {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.no-category {
  color: #c0c4cc;
  font-size: 13px;
}
</style>
