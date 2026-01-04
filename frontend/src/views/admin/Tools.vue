<template>
  <div class="tools-page">
    <!-- 操作栏 -->
    <div class="toolbar">
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>
        添加工具
      </el-button>
      <el-button @click="showImportDialog">
        <el-icon><Upload /></el-icon>
        批量导入
      </el-button>
      <el-button text @click="downloadTemplate">
        <el-icon><Download /></el-icon>
        下载模板
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
      <el-table-column prop="provider" label="提供者" width="100" />
      <el-table-column prop="description" label="描述" show-overflow-tooltip />
      <el-table-column label="分类" width="120">
        <template #default="{ row }">
          <el-tag v-if="row.category" size="small" :color="row.category.color" effect="dark">
            {{ row.category.name }}
          </el-tag>
          <span v-else class="no-category">未分类</span>
        </template>
      </el-table-column>
      <el-table-column label="标签" min-width="150">
        <template #default="{ row }">
          <div class="tag-cell" v-if="row.tags?.length">
            <el-tag
              v-for="tag in row.tags"
              :key="tag.id"
              size="small"
              :style="{ background: tag.color, borderColor: tag.color }"
              effect="dark"
            >
              {{ tag.name }}
            </el-tag>
          </div>
          <span v-else class="no-category">-</span>
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
          <el-button type="danger" text size="small" @click="handleDeleteClick(row)">
            删除
          </el-button>
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
        <el-form-item label="提供者" prop="provider">
          <el-input v-model="formData.provider" placeholder="谁推荐了这个工具？" />
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
        <el-form-item label="标签">
          <el-select
            v-model="selectedTagIds"
            multiple
            placeholder="选择标签"
            style="width: 100%"
          >
            <el-option
              v-for="tag in allTags"
              :key="tag.id"
              :label="tag.name"
              :value="tag.id"
            >
              <span class="tag-option">
                <span class="tag-dot" :style="{ background: tag.color }"></span>
                {{ tag.name }}
              </span>
            </el-option>
          </el-select>
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

    <!-- 导入弹窗 -->
    <el-dialog v-model="importDialogVisible" title="批量导入工具" width="500px">
      <el-upload
        ref="uploadRef"
        drag
        :auto-upload="false"
        :limit="1"
        accept=".xlsx,.xls"
        :on-change="handleFileChange"
        :on-exceed="handleExceed"
      >
        <el-icon class="el-icon--upload"><Upload /></el-icon>
        <div class="el-upload__text">
          拖拽文件到此处，或 <em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            仅支持 .xlsx 格式，
            <el-link type="primary" @click="downloadTemplate">下载模板</el-link>
          </div>
        </template>
      </el-upload>

      <el-checkbox v-model="importUpdateExisting" style="margin-top: 16px">
        更新已存在的工具（按名称匹配）
      </el-checkbox>

      <div v-if="importResult" class="import-result">
        <el-alert
          :type="importResult.errors.length > 0 ? 'warning' : 'success'"
          :closable="false"
        >
          <template #title>
            导入完成：新增 {{ importResult.created }}，
            更新 {{ importResult.updated }}，
            跳过 {{ importResult.skipped }}
          </template>
          <template #default v-if="importResult.errors.length > 0">
            <div class="import-errors">
              <div v-for="(err, i) in importResult.errors" :key="i">{{ err }}</div>
            </div>
          </template>
        </el-alert>
      </div>

      <template #footer>
        <el-button @click="importDialogVisible = false">关闭</el-button>
        <el-button
          type="primary"
          @click="handleImport"
          :loading="importing"
          :disabled="!importFile"
        >
          开始导入
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Upload, Download } from '@element-plus/icons-vue'
import { adminApi } from '@/api'

const loading = ref(false)
const submitting = ref(false)
const tools = ref([])
const categories = ref([])
const allTags = ref([])
const total = ref(0)
const page = ref(1)
const size = ref(20)
const filterCategoryId = ref(null)
const selectedTagIds = ref([])

const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const formRef = ref(null)
const categoryPath = ref(null)

// 导入相关
const importDialogVisible = ref(false)
const importing = ref(false)
const importFile = ref(null)
const importUpdateExisting = ref(true)
const importResult = ref(null)
const uploadRef = ref(null)

const formData = reactive({
  name: '',
  description: '',
  icon_url: '',
  target_url: '',
  provider: '',
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
  await Promise.all([loadCategories(), loadTags()])
  await loadTools()
})

async function loadTags() {
  try {
    const res = await adminApi.getTags()
    allTags.value = res.items || []
  } catch (error) {
    console.error('加载标签失败:', error)
  }
}

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

async function handleEdit(row) {
  isEdit.value = true
  editId.value = row.id
  Object.assign(formData, {
    name: row.name,
    description: row.description || '',
    icon_url: row.icon_url || '',
    target_url: row.target_url,
    provider: row.provider || '',
    category_id: row.category_id,
    sort_order: row.sort_order || 0,
    is_active: row.is_active
  })
  categoryPath.value = row.category_id
  // 加载工具的标签
  try {
    const tags = await adminApi.getToolTags(row.id)
    selectedTagIds.value = tags.map(t => t.id)
  } catch (error) {
    console.error('加载工具标签失败:', error)
    selectedTagIds.value = []
  }
  dialogVisible.value = true
}

async function handleSubmit() {
  try {
    await formRef.value.validate()
    submitting.value = true

    let toolId
    if (isEdit.value) {
      await adminApi.updateTool(editId.value, formData)
      toolId = editId.value
      ElMessage.success('更新成功')
    } else {
      const result = await adminApi.createTool(formData)
      toolId = result.id
      ElMessage.success('创建成功')
    }

    // 保存标签
    if (toolId) {
      await adminApi.setToolTags(toolId, selectedTagIds.value)
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

async function handleDeleteClick(row) {
  try {
    // 先获取删除影响预览
    const preview = await adminApi.previewDeleteTool(row.id)

    let message = `确定删除工具 <strong>${row.name}</strong> ？`
    if (preview.total > 0) {
      message += `<br/><br/><span style="color: #E6A23C;">⚠️ 将同时删除以下关联数据：</span>`
      message += `<ul style="margin: 8px 0 0 20px; padding: 0;">`
      if (preview.favorites > 0) message += `<li>${preview.favorites} 条收藏记录</li>`
      if (preview.likes > 0) message += `<li>${preview.likes} 条点赞记录</li>`
      if (preview.clicks > 0) message += `<li>${preview.clicks} 条点击记录</li>`
      message += `</ul>`
    }

    await ElMessageBox.confirm(message, '删除确认', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
      dangerouslyUseHTMLString: true,
    })

    await handleDelete(row.id)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除预检失败:', error)
      ElMessage.error('操作失败')
    }
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
    provider: '',
    category_id: null,
    sort_order: 0,
    is_active: true
  })
  categoryPath.value = null
  selectedTagIds.value = []
}

// ============ 导入相关 ============

function showImportDialog() {
  importFile.value = null
  importResult.value = null
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
  importDialogVisible.value = true
}

function handleFileChange(file) {
  importFile.value = file.raw
}

function handleExceed() {
  ElMessage.warning('只能上传一个文件，请先删除已选文件')
}

async function handleImport() {
  if (!importFile.value) return

  try {
    importing.value = true
    const result = await adminApi.importTools(importFile.value, importUpdateExisting.value)
    importResult.value = result
    ElMessage.success(`导入完成：新增 ${result.created}，更新 ${result.updated}`)
    loadTools()
  } catch (error) {
    console.error('导入失败:', error)
    ElMessage.error(error.response?.data?.detail || '导入失败')
  } finally {
    importing.value = false
  }
}

async function downloadTemplate() {
  try {
    const blob = await adminApi.downloadTemplate()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'tools_import_template.xlsx'
    a.click()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('下载模板失败:', error)
    ElMessage.error('下载模板失败')
  }
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

.import-result {
  margin-top: 16px;
}

.import-errors {
  margin-top: 8px;
  font-size: 12px;
  color: #e6a23c;
  max-height: 150px;
  overflow-y: auto;
}

.tag-cell {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.tag-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tag-dot {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  flex-shrink: 0;
}
</style>
