import { createRoute } from '@tanstack/react-router'
import { Route as rootRoute } from './__root'
import App from '../App'

export const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: App,
})
