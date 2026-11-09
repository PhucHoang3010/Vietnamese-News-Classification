// Tiện ích dùng chung cho 2 bộ slide: icon (react-icons → PNG), kích thước ảnh giữ tỉ lệ.
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const path = require("path");

const ASSETS = path.join(__dirname, "assets");
const REPORT_IMG = path.join(__dirname, "..", "report_images");
const DIAGRAMS = path.join(__dirname, "..", "images");

async function iconPng(Icon, hex, size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Icon, { color: `#${hex}`, size }));
  const buf = await sharp(Buffer.from(svg)).resize(size, size).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

async function imageSize(file) {
  const meta = await sharp(file).metadata();
  return { w: meta.width, h: meta.height };
}

// Đặt ảnh vừa khung (contain), canh giữa trong khung
async function fitImage(slide, file, box, opts = {}) {
  const { w, h } = await imageSize(file);
  const scale = Math.min(box.w / w, box.h / h);
  const iw = w * scale;
  const ih = h * scale;
  const x = box.x + (opts.align === "left" ? 0 : (box.w - iw) / 2);
  const y = box.y + (opts.valign === "top" ? 0 : (box.h - ih) / 2);
  slide.addImage({ path: file, x, y, w: iw, h: ih, altText: opts.alt || "", objectName: opts.name });
  return { x, y, w: iw, h: ih };
}

module.exports = { iconPng, fitImage, ASSETS, REPORT_IMG, DIAGRAMS };
