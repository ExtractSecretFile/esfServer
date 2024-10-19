# esfServer

ESF 授权服务器

## Setup

- 启动 Redis v7+
    - Windows: [`redis-windows`](https://github.com/redis-windows/redis-windows)
    - Other: 自己谷歌搜
- 按需修改 `.env`

### 安装python依赖

```bash
python3 -m pip install -r requirements.txt 
```

## Usage

### 生成序列号

```bash
# 一码一机
python3 gen_serial.py 100000 > serials.txt
# 一码多机
python3 gen_serial_times.py 1000 100 > serials_multi_100.txt
python3 gen_serial_times.py 1000 500 > serials_multi_500.txt
python3 gen_serial_times.py 1000 1000 > serials_multi_1000.txt
```

### 启动服务器

```bash
python3 server.py
```

## For End-Users

请保护好您的激活码、机器码，请勿分享于他人

激活码、机器码被视为用户隐私信息，可用于查询注册历史，包含注册时间、注册IP、所用机器码。

## Support

联系 `mokurin000` 可以咨询获取付费支持、提取脚本