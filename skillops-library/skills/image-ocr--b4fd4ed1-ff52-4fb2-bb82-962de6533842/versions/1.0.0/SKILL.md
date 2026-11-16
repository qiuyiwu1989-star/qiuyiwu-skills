# Image OCR - 图片文字识别

## 什么时候用
- 用户发来图片（截图、文档照片、PPT截图、聊天截图等），需要提取其中的文字
- 模型不支持多模态时，作为图片理解的fallback

## 使用流程

### 1. 下载图片
用户发来的图片需要先下载到本地。使用 `feishu_im_bot_image` 工具：
```
feishu_im_bot_image(message_id=<从上下文获取>, file_key=<图片的image_key>, type="image")
```
返回的 `saved_path` 就是本地路径。

### 2. 运行OCR
```bash
python3 /root/.openclaw/workspace/skills/image-ocr/ocr.py <saved_path>
```

### 3. 返回结果
- 将OCR结果整理后返回给用户
- 如果图片中文字很多，可以适当分段
- 如果识别效果差，建议用户重新截图或发更清晰的图片

## 语言支持
- `chi_sim+eng`（默认）：简体中文 + 英文
- `chi_sim`：仅简体中文
- `chi_tra+eng`：繁体中文 + 英文
- `eng`：仅英文

可加 `--lang` 参数指定：
```bash
python3 ocr.py image.png --lang eng
```

## 限制
- 手写体识别效果一般
- 低分辨率/模糊图片可能识别不准
- 表格/复杂排版可能丢失结构
- 不支持PDF直接处理（需先转图片）

## 依赖
- tesseract-ocr（已安装）
- tesseract-ocr-chi-sim / chi-tra / eng（已安装）
- pytesseract（Python wrapper，已安装）
- Pillow（已安装，用于预处理）
