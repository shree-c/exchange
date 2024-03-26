import { AxiosError } from 'axios'
import { useToast } from 'primevue/usetoast'
export const useNetworkWrapper = () => {
  const toast = useToast()
  async function networkWrapper(cb: () => Promise<any>) {
    try {
      return await cb()
    } catch (error) {
      if (error instanceof AxiosError) {
        if (error.response) {
          if (error.response?.status == 400) {
            const message = error.response?.data?.data?.message
              ? error.response?.data?.data?.message
              : 'Client error: unknown cause'
            toast.add({
              severity: 'error',
              summary: message,
              life: 3000
            })
          } else if (error.response?.status === 500) {
            toast.add({
              severity: 'error',
              summary: error.response?.data?.message || 'Server error: unknown cause',
              life: 3000
            })
          } else if (error.response?.status === 422) {
            toast.add({
              severity: 'error',
              summary: "Frontend developer error. Sending wrong request. Check console",
            })
            console.log(error)
          } else {
            toast.add({
              severity: 'error',
              summary: `An unhandled error with response code: ${error.response?.status} happened.`
            })
          }
        } else if (error.request) {
          toast.add({
            severity: 'error',
            summary: 'No response received from the server',
            life: 3000
          })
          console.log(error.request)
        } else {
          // Something happened in setting up the request that triggered an Error
          toast.add({
            severity: 'error',
            summary: "Couldn't make request please check your internet connection",
            life: 3000
          })
        }
        console.log(error)
      } else {
        toast.add({
          severity: 'error',
          summary: "Couldn't make request please check your internet connection",
          life: 3000
        })
        console.log(error)
      }
    }
  }
  return { networkWrapper, toast }
}
