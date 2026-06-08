import { useState } from 'react'

function App() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [error, setError] = useState('')

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault()
    if (email === 'admin@quantyfin.ai' && password === 'password123') {
      setIsLoggedIn(true)
      setError('')
    } else {
      setError('Sai email hoặc mật khẩu!')
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12 dark:bg-gray-900 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8 rounded-2xl border border-gray-200 bg-white p-8 shadow-sm dark:border-gray-800 dark:bg-gray-950">
        {!isLoggedIn ? (
          <div>
            <div className="text-center">
              <h1 className="text-2xl font-bold tracking-tight text-gray-900 dark:text-white font-heading">
                QuantyFin AI
              </h1>
              <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                Đăng nhập để vào hệ thống Command Center
              </p>
            </div>
            <form className="mt-8 space-y-6" onSubmit={handleLogin}>
              <div className="space-y-4 rounded-md">
                <div>
                  <label htmlFor="email-address" className="sr-only">Email</label>
                  <input
                    id="email-address"
                    name="email"
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="relative block w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 placeholder-gray-500 focus:z-10 focus:border-primary focus:outline-none focus:ring-primary dark:border-gray-800 dark:bg-gray-900 dark:text-white sm:text-sm"
                    placeholder="Email (admin@quantyfin.ai)"
                  />
                </div>
                <div>
                  <label htmlFor="password" className="sr-only">Mật khẩu</label>
                  <input
                    id="password"
                    name="password"
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="relative block w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 placeholder-gray-500 focus:z-10 focus:border-primary focus:outline-none focus:ring-primary dark:border-gray-800 dark:bg-gray-900 dark:text-white sm:text-sm"
                    placeholder="Mật khẩu (password123)"
                  />
                </div>
              </div>

              {error && (
                <div className="text-sm text-red-600 dark:text-red-400" id="error-message">
                  {error}
                </div>
              )}

              <div>
                <button
                  type="submit"
                  className="group relative flex w-full justify-center rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
                >
                  Đăng nhập
                </button>
              </div>
            </form>
          </div>
        ) : (
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white" id="welcome-message">
              Chào mừng bạn đến với QuantyFin!
            </h1>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
              Bạn đã đăng nhập thành công vào hệ thống.
            </p>
            <button
              onClick={() => setIsLoggedIn(false)}
              className="mt-6 rounded-lg border border-gray-300 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 dark:border-gray-800 dark:text-gray-300 dark:hover:bg-gray-900"
            >
              Đăng xuất
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
