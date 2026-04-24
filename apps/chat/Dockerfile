FROM golang:1.25-alpine AS build
WORKDIR /src
COPY go.mod ./
COPY go.sum* ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags "-s -w" -o /out/chat .

FROM gcr.io/distroless/static-debian12:nonroot
WORKDIR /
COPY --from=build /out/chat /chat
USER nonroot:nonroot
EXPOSE 8090
HEALTHCHECK NONE
ENTRYPOINT ["/chat"]
