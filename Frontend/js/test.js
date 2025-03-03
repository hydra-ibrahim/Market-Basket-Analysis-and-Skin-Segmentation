document.getElementById('fileInput').addEventListener('change', function (event) {
    const file = event.target.files[0];
    const reader = new FileReader();

    reader.onload = function (e) {
        const image = new Image();
        image.src = e.target.result;
        image.onload = function () {
            const canvas = document.getElementById('canvas');
            const ctx = canvas.getContext('2d', { willReadFrequently: true });
            canvas.width = image.width;
            canvas.height = image.height;
            canvas.willReadFrequently = true;
            ctx.drawImage(image, 0, 0, canvas.width, canvas.height);

            canvas.addEventListener('click', function (e) {
                const x = e.offsetX;
                const y = e.offsetY;
                const imageData = ctx.getImageData(x, y, 1, 1);
                const pixel = imageData.data;

                // const rgb = `(${pixel[0]}, ${pixel[1]}, ${pixel[2]})`;
                // document.getElementById('rgbValues').textContent = rgb;

                document.getElementById('redValue').textContent = pixel[0];
                document.getElementById('greenValue').textContent = pixel[1];
                document.getElementById('blueValue').textContent = pixel[2];
                console.log(pixel[0],pixel[1],pixel[2])
                getTheResult(pixel[0], pixel[1], pixel[2])
            });
        };
    };

    reader.readAsDataURL(file);
});

function getTheResult(R, G, B) {
    fetch(`http://127.0.0.1:8000/knn/image/${R}/${G}/${B}/`).then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
        .then(data => {
            console.log(data[1])

            document.getElementById('result').innerText = data[1] == '1' ? 'Skin' : 'Non-skin'
        })
        .catch(error => {
            console.error('Error:', error);
        });
}
