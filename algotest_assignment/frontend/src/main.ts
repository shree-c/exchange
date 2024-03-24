import './assets/main.css'

import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import Primevue from 'primevue/config'
import ToastService  from 'primevue/toastservice'
import 'primevue/resources/themes/aura-dark-green/theme.css'

const app = createApp(App)

app.use(router)

app.mount('#app')
app.use(Primevue)
app.use(ToastService)