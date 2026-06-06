# Hướng dẫn Triển khai (Deployment Guide)

Tài liệu này hướng dẫn cách đóng gói và triển khai ứng dụng QuantyFin Frontend lên các môi trường lưu trữ sản xuất (production hosting). Vì đây là một ứng dụng Single Page Application (SPA) xây dựng bằng Vite, sản phẩm đầu ra sau khi biên dịch là các tệp tĩnh (HTML, JS, CSS) hoàn toàn có thể chạy độc lập.

## 1. Biên dịch và Đóng gói (Build Package)

Trước khi triển khai, bạn cần chạy lệnh biên dịch trên môi trường phát triển hoặc trong máy chủ CI:

```bash
# Di chuyển vào thư mục dự án
cd docs/sample_src/frontend

# Thực hiện biên dịch tối ưu hóa
npm run build
```

* **Kết quả đầu ra:** Toàn bộ mã nguồn đã được tối ưu hóa sẽ được xuất ra thư mục `docs/sample_src/frontend/dist/`.
* **Cấu trúc bản build:**
  * `index.html`: Điểm nhập ứng dụng đã được liên kết các bundle JS/CSS.
  * `assets/`: Chứa các file javascript và css đã nén và chia nhỏ (code splitting).
  * `favicon.svg` & `icons.svg`: Các tài nguyên tĩnh được sao chép trực tiếp.

## 2. Các phương án triển khai chính (Deployment Options)

### Phương án A: Triển khai lên Vercel (Khuyến nghị)
Vercel hỗ trợ cấu hình tự động rất tốt cho các dự án Vite.

1. Đăng nhập vào [Vercel Dashboard](https://vercel.com).
2. Tạo dự án mới và liên kết với kho lưu trữ Git của bạn.
3. Cấu hình cài đặt dự án (Project Settings):
   * **Framework Preset:** Chọn `Vite`.
   * **Root Directory:** Chọn `docs/sample_src/frontend`.
   * **Build Command:** `npm run build`
   * **Output Directory:** `dist`
4. Bấm **Deploy**. Vercel sẽ tự động tải các gói phụ thuộc, biên dịch và cấp tên miền công khai.

### Phương án B: Triển khai lên Netlify
1. Đăng nhập vào [Netlify](https://netlify.com).
2. Tạo trang web mới từ kho Git.
3. Thiết lập thông số build:
   * **Base directory:** `docs/sample_src/frontend`
   * **Build command:** `npm run build`
   * **Publish directory:** `docs/sample_src/frontend/dist`
4. Bấm **Deploy site**.

### Phương án C: Triển khai lên Docker (Containerization)
Nếu dự án cần được chạy trong môi trường Container của Kubernetes hoặc Docker Compose:

1. Sử dụng tệp `Dockerfile` mẫu sau tại thư mục `docs/sample_src/frontend/`:
```dockerfile
# Stage 1: Build ứng dụng
FROM node:20-alpine AS build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Stage 2: Cấu hình Web Server Nginx để phục vụ file tĩnh
FROM nginx:stable-alpine AS production-stage
COPY --from=build-stage /app/dist /usr/share/nginx/html
# Bổ sung cấu hình Nginx để định tuyến SPA hoạt động bình thường
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

2. Tệp cấu hình Nginx tối thiểu (`nginx.conf`) để hỗ trợ React SPA Routing:
```nginx
server {
    listen 80;
    server_name localhost;

    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }
}
```

## 3. Cấu hình DNS và SSL
Sau khi triển khai thành công lên các dịch vụ máy chủ tĩnh, cần:
1. Trỏ bản ghi CNAME hoặc A của tên miền tùy chỉnh của bạn tới địa chỉ IP của nhà cung cấp dịch vụ Host.
2. Kích hoạt chứng chỉ SSL/TLS miễn phí (thường được tự động cấp bởi Vercel/Netlify qua Let's Encrypt) để bảo vệ kết nối người dùng qua HTTPS.
