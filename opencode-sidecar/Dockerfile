FROM node:20-alpine

RUN apk add --no-cache curl bash jq

RUN curl -fsSL https://opencode.ai/install | bash

ENV PATH="/root/.opencode/bin:${PATH}"

WORKDIR /app

COPY startup.sh /app/startup.sh
RUN chmod +x /app/startup.sh

EXPOSE 4096

ENTRYPOINT ["/app/startup.sh"]
