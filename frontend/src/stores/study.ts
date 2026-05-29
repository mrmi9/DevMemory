import { defineStore } from 'pinia'
import { api, type Course } from '../api'

export const useStudyStore = defineStore('study', {
  state: () => ({
    courses: [] as Course[],
    selectedCourseId: '',
    progressRefreshKey: 0,
    busy: false,
    error: ''
  }),
  getters: {
    selectedCourse: (state) => state.courses.find((course) => course.id === state.selectedCourseId)
  },
  actions: {
    async login(username = 'admin', password = 'changeme') {
      await api.login(username, password)
    },
    logout() {
      api.logout()
      this.courses = []
      this.selectedCourseId = ''
      this.progressRefreshKey = 0
      this.busy = false
      this.error = ''
    },
    async loadCourses() {
      this.error = ''
      try {
        this.courses = await api.listCourses()
        if (!this.selectedCourseId && this.courses.length) {
          this.selectedCourseId = this.courses[0].id
        }
      } catch (error) {
        this.error = error instanceof Error ? error.message : String(error)
      }
    },
    async createCourse(title: string, description: string) {
      this.busy = true
      try {
        const palette = ['#2563eb', '#059669', '#dc2626', '#7c3aed', '#b45309']
        const course = await api.createCourse({ title, description, color: palette[this.courses.length % palette.length] })
        this.courses.unshift(course)
        this.selectedCourseId = course.id
      } finally {
        this.busy = false
      }
    },
    async deleteCourse(courseId: string) {
      this.busy = true
      this.error = ''
      try {
        await api.deleteCourse(courseId)
        this.courses = this.courses.filter((course) => course.id !== courseId)
        if (this.selectedCourseId === courseId) {
          this.selectedCourseId = this.courses[0]?.id ?? ''
        }
      } catch (error) {
        this.error = error instanceof Error ? error.message : String(error)
        throw error
      } finally {
        this.busy = false
      }
    },
    markProgressChanged() {
      this.progressRefreshKey += 1
    }
  }
})
