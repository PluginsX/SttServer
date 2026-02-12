const fs = require('fs');

// 读取修改后的AsrClient.js文件
const filePath = 'f:\\Project\\Python\\AsrServer\\Client\\Web\\demo\\js\\lib\\AsrClient.js';
const content = fs.readFileSync(filePath, 'utf8');

console.log('检查LocalAsrAdapter构造函数中是否包含参数定义...');
const constructorMatch = content.match(/constructor\(options = \{\}\) \{[\s\S]*?this\.maxSentenceSilence = options\.maxSentenceSilence \|\| 800;/);
if (constructorMatch) {
    console.log('✅ 构造函数中已包含参数定义');
} else {
    console.log('❌ 构造函数中未找到参数定义');
}

console.log('\n检查LocalAsrAdapter startRecognition方法中是否使用动态参数...');
const startRecMatch = content.match(/enable_punctuation_prediction: this\.punctuationPredictionEnabled/);
if (startRecMatch) {
    console.log('✅ startRecognition方法中使用了动态参数');
} else {
    console.log('❌ startRecognition方法中未使用动态参数');
}

console.log('\n检查是否添加了response_mode参数...');
const responseModeMatch = content.match(/response_mode: 'fast'/);
if (responseModeMatch) {
    console.log('✅ 已添加response_mode参数');
} else {
    console.log('❌ 未添加response_mode参数');
}

console.log('\n验证修改结果完成！');