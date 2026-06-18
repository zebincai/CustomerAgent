FROM python:3.12.13-slim-bookworm

# 创建一个非 root 用户，Hugging Face 要求 UID 为 1000
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# 复制文件
COPY --chown=user . $HOME/app

# 安装依赖
RUN pip install --no-cache-dir .

# 暴露 Hugging Face 指定的 7860 端口
EXPOSE 7860

# 启动命令：必须监听 0.0.0.0:7860
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]