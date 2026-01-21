/**
 * PDF Export Utility
 * Uses html2pdf.js to export HTML elements to PDF
 */

import html2pdf from 'html2pdf.js';

export interface PDFExportOptions {
    filename?: string;
    margin?: number;
    pageFormat?: 'a4' | 'letter' | 'legal';
    orientation?: 'portrait' | 'landscape';
    quality?: number;
    scale?: number;
}

const defaultOptions: PDFExportOptions = {
    filename: 'report',
    margin: 10,
    pageFormat: 'a4',
    orientation: 'portrait',
    quality: 0.98,
    scale: 2,
};

/**
 * Export a DOM element to PDF
 * @param elementId - ID of the element to export
 * @param options - PDF export options
 */
export async function exportToPDF(
    elementId: string,
    options: PDFExportOptions = {}
): Promise<void> {
    const element = document.getElementById(elementId);

    if (!element) {
        console.error(`Element with ID "${elementId}" not found`);
        throw new Error(`Element with ID "${elementId}" not found`);
    }

    const finalOptions = { ...defaultOptions, ...options };
    const timestamp = new Date().toISOString().split('T')[0];

    // Show PDF-only header before export
    const pdfHeader = element.querySelector('.pdf-only-header') as HTMLElement;
    if (pdfHeader) {
        pdfHeader.style.display = 'block';
    }

    // Store original styles to restore later
    const originalBg = element.style.backgroundColor;
    const originalColor = element.style.color;
    
    // Apply light theme for PDF (dark text on white background)
    element.style.backgroundColor = '#ffffff';
    element.style.color = '#1a1a2e';
    
    // Apply dark text to all text elements for PDF visibility
    const textElements = element.querySelectorAll('*');
    const originalStyles: Map<Element, { color: string; backgroundColor: string }> = new Map();
    
    textElements.forEach((el) => {
        const htmlEl = el as HTMLElement;
        originalStyles.set(el, {
            color: htmlEl.style.color,
            backgroundColor: htmlEl.style.backgroundColor
        });
        
        // Force dark text colors for PDF readability
        const computedColor = window.getComputedStyle(htmlEl).color;
        if (computedColor && (computedColor.includes('255') || computedColor.includes('rgb(255') || computedColor.includes('rgba(255'))) {
            htmlEl.style.color = '#1a1a2e';
        }
        
        // Handle specific element types
        if (htmlEl.tagName === 'H1' || htmlEl.tagName === 'H2' || htmlEl.tagName === 'H3') {
            htmlEl.style.color = '#1a1a2e';
        }
        if (htmlEl.tagName === 'P' || htmlEl.tagName === 'SPAN' || htmlEl.tagName === 'DIV') {
            if (!htmlEl.style.color || htmlEl.style.color.includes('var(')) {
                htmlEl.style.color = '#2d2d3a';
            }
        }
        
        // Make backgrounds white/transparent
        const computedBg = window.getComputedStyle(htmlEl).backgroundColor;
        if (computedBg && computedBg !== 'rgba(0, 0, 0, 0)' && computedBg !== 'transparent') {
            if (computedBg.includes('rgb(') && !computedBg.includes('255, 255, 255')) {
                htmlEl.style.backgroundColor = 'rgba(240, 240, 245, 0.5)';
            }
        }
    });

    const pdfOptions = {
        margin: finalOptions.margin,
        filename: `${finalOptions.filename}_${timestamp}.pdf`,
        image: { type: 'jpeg' as const, quality: finalOptions.quality },
        html2canvas: {
            scale: finalOptions.scale,
            useCORS: true,
            logging: false,
            backgroundColor: '#ffffff'
        },
        jsPDF: {
            unit: 'mm' as const,
            format: finalOptions.pageFormat,
            orientation: finalOptions.orientation
        },
        pagebreak: { mode: ['avoid-all', 'css', 'legacy'] }
    };

    try {
        await html2pdf().set(pdfOptions).from(element).save();
    } catch (error) {
        console.error('PDF export failed:', error);
        throw error;
    } finally {
        // Restore original styles
        element.style.backgroundColor = originalBg;
        element.style.color = originalColor;
        
        textElements.forEach((el) => {
            const htmlEl = el as HTMLElement;
            const original = originalStyles.get(el);
            if (original) {
                htmlEl.style.color = original.color;
                htmlEl.style.backgroundColor = original.backgroundColor;
            }
        });
        
        // Hide PDF-only header after export
        if (pdfHeader) {
            pdfHeader.style.display = 'none';
        }
    }
}

/**
 * Export element to PDF with print-friendly styling
 * Temporarily applies print styles before exporting
 */
export async function exportWithPrintStyles(
    elementId: string,
    options: PDFExportOptions = {}
): Promise<void> {
    const element = document.getElementById(elementId);
    if (!element) {
        throw new Error(`Element with ID "${elementId}" not found`);
    }

    // Add print class for styling
    element.classList.add('pdf-export-mode');

    // Wait for styles to apply
    await new Promise(resolve => setTimeout(resolve, 100));

    try {
        await exportToPDF(elementId, options);
    } finally {
        // Remove print class
        element.classList.remove('pdf-export-mode');
    }
}

/**
 * Generate a formatted date range string for reports
 */
export function getReportDateRange(period: string): string {
    const now = new Date();
    let startDate: Date;

    switch (period) {
        case '7d':
            startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
            break;
        case '30d':
            startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
            break;
        case '90d':
            startDate = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);
            break;
        case '1y':
            startDate = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000);
            break;
        default:
            startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
    }

    const formatDate = (d: Date) => d.toLocaleDateString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
    });

    return `${formatDate(startDate)} - ${formatDate(now)}`;
}
