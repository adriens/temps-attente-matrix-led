const puppeteer = require('puppeteer');
const PDFDocument = require('pdfkit');
const fs = require('fs');

(async () => {
    const browser = await puppeteer.launch({
        executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', // Vérifie le chemin de Chrome
        headless: true,
        defaultViewport: { width: 1920, height: 1080 }
    });

    const page = await browser.newPage();

    try {
        console.log("Accès à la présentation Reveal.js...");
        await page.goto('http://192.168.1.201:1947/', {
            waitUntil: 'networkidle2',
            timeout: 60000
        });

        // Attendre que tout se charge
        await new Promise(resolve => setTimeout(resolve, 3000));

        // Récupérer le nombre total de slides horizontales
        const totalHorizontales = await page.evaluate(() => Reveal.getHorizontalSlides().length);
        let slideGrid = [];

        for (let h = 0; h < totalHorizontales; h++) {
            Reveal.slide(h, 0); // Se positionner sur la slide horizontale
            const totalVerticales = Math.min(8, Reveal.getVerticalSlides(h).length); // Max 8 verticales
            for (let v = 0; v <= totalVerticales; v++) {
                slideGrid.push({ h, v });
            }
        }

        console.log(`Total des slides détectées : ${slideGrid.length}`);

        // Création du PDF
        const doc = new PDFDocument({ size: 'A4', layout: 'landscape' });
        const pdfStream = fs.createWriteStream('presentation.pdf');
        doc.pipe(pdfStream);

        for (let i = 0; i < slideGrid.length; i++) {
            const { h, v } = slideGrid[i];
            console.log(`Capture de la slide ${i + 1} / ${slideGrid.length} (h: ${h}, v: ${v})`);

            // Aller à la slide correspondante
            await page.evaluate((h, v) => {
                Reveal.slide(h, v);
            }, h, v);

            // Attendre l'animation
            await new Promise(resolve => setTimeout(resolve, 1000));

            // Capturer l'image et enregistrer sur disque
            const screenshotPath = `slide-${i + 1}.png`;
            await page.screenshot({ path: screenshotPath, fullPage: false });

            // Ajouter l'image au PDF
            doc.addPage().image(screenshotPath, 50, 50, { width: 700 });

            console.log(`Slide ${i + 1} capturée.`);
        }

        // Finaliser le PDF
        doc.end();

        console.log("PDF généré avec succès !");
    } catch (error) {
        console.error("Erreur lors de la capture :", error);
    } finally {
        await browser.close();
    }
})();
