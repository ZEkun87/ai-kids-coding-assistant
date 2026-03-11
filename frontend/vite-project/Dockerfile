# 构建阶段
FROM node:18-alpine as build

WORKDIR /app

# 复制包管理文件
COPY package.json package-lock.json ./

# 安装依赖（国内源）
RUN npm install --registry=https://registry.npmmirror.com

# 复制前端代码
COPY . .

# 构建生产包
RUN npm run build

# 运行阶段
FROM nginx:alpine

# 复制构建产物
COPY --from=build /app/dist /usr/share/nginx/html

# 暴露端口
EXPOSE 80

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]