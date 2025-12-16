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
