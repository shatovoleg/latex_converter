const fileInput = document.getElementById('pdf-upload');
const fileLabelText = document.getElementById('file-label-text');
const convertBtn = document.getElementById('convert-btn');
const statusDiv = document.getElementById('status');
const errorDiv = document.getElementById('error');
const downloadLink = document.getElementById('download-link');

let selectedFile = null;

fileInput.addEventListener('change', (e) => {
    selectedFile = e.target.files[0];
    fileLabelText.textContent = selectedFile ? selectedFile.name : 'Выберите PDF-файл';
    convertBtn.disabled = !selectedFile;
    statusDiv.textContent = '';
    errorDiv.textContent = '';
    downloadLink.style.display = 'none';
    console.log('[fileInput] selectedFile:', selectedFile);
});

convertBtn.addEventListener('click', async () => {
    if (!selectedFile) return;

    convertBtn.disabled = true;
    statusDiv.textContent = 'Загрузка PDF...';
    errorDiv.textContent = '';
    downloadLink.style.display = 'none';

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
        console.log('[convertBtn] Отправка файла:', selectedFile.name);
        // 1. Загрузка PDF
        const uploadResponse = await fetch('http://77.234.216.102:17625/tatneft/api/v1/convert', {
            method: 'POST',
            body: formData,
        });
        console.log('[convertBtn] uploadResponse status:', uploadResponse.status);

        if (!uploadResponse.ok) {
            const errorData = await uploadResponse.json().catch(() => ({}));
            console.log('[convertBtn] uploadResponse errorData:', errorData);
            throw new Error(`Ошибка загрузки: ${uploadResponse.status} ${uploadResponse.statusText}. ${errorData.detail || ''}`);
        }

        const result = await uploadResponse.json();
        console.log('[convertBtn] uploadResponse result:', result);
        const downloadUrl = result.download_url;
        if (!downloadUrl) throw new Error('Не получен путь для скачивания.');
        
        // Извлекаем ID из пути /convert/{id}
        const convertId = downloadUrl.split('/').pop();
        if (!convertId) throw new Error('Не удалось получить ID конвертации.');
        console.log('[convertBtn] convertId:', convertId);

        statusDiv.textContent = 'Конвертация...';

        // 2. Скачивание ZIP
        const resultUrl = `http://77.234.216.102:17625/tatneft/api/v1/convert/${convertId}`;
        console.log('[convertBtn] resultUrl:', resultUrl);
        const zipResponse = await fetch(resultUrl);
        console.log('[convertBtn] zipResponse status:', zipResponse.status);

        // Проверяем ответ
        if (!zipResponse.ok) {
            let errorMsg = `Ошибка скачивания: ${zipResponse.status} ${zipResponse.statusText}.`;
            try {
                const errorData = await zipResponse.json();
                console.log('[convertBtn] zipResponse errorData:', errorData);
                errorMsg += ' ' + (errorData.detail || JSON.stringify(errorData));
            } catch {
                // Не JSON, возможно просто текст ошибки
                const text = await zipResponse.text();
                console.log('[convertBtn] zipResponse text:', text);
                errorMsg += ' ' + text;
            }
            throw new Error(errorMsg);
        }

        const blob = await zipResponse.blob();
        console.log('[convertBtn] zipResponse blob:', blob);
        const url = URL.createObjectURL(blob);
        downloadLink.href = url;
        downloadLink.download = `converted_${selectedFile.name.replace('.pdf', '')}.zip`;
        downloadLink.style.display = 'inline-block';
        statusDiv.textContent = 'Готово! Загрузите результат:';
        console.log('[convertBtn] Файл готов к скачиванию:', url);
    } catch (err) {
        errorDiv.textContent = err.message;
        statusDiv.textContent = '';
        console.log('[convertBtn] Ошибка:', err);
    } finally {
        convertBtn.disabled = false;
    }
});