FROM n8nio/n8n:2.5.0

# 静态 ffmpeg 构建 (支持 amd64 / arm64 自适应)
USER root
ARG TARGETARCH=amd64
RUN FFARCH=${TARGETARCH} \
    && wget -q --timeout=60 --tries=3 \
       "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-${FFARCH}-static.tar.xz" \
       -O /tmp/ffmpeg.tar.xz \
    && tar -xJf /tmp/ffmpeg.tar.xz -C /tmp \
    && mv /tmp/ffmpeg-*-${FFARCH}-static/ffmpeg /usr/local/bin/ \
    && mv /tmp/ffmpeg-*-${FFARCH}-static/ffprobe /usr/local/bin/ \
    && chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe \
    && rm -rf /tmp/ffmpeg*

USER node
