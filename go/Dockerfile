FROM golang:1.25-alpine AS builder
WORKDIR /src
COPY go.mod ./
RUN go mod download 2>/dev/null || true
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /out/sconvert-server ./cmd/server

FROM gcr.io/distroless/static-debian12
COPY --from=builder /out/sconvert-server /sconvert-server
EXPOSE 8080
ENTRYPOINT ["/sconvert-server"]
