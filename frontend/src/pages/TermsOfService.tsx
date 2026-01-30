/**
 * Terms of Service Page - DataVision Enterprise Analytics Platform
 * Last updated: January 2025
 */

import React from 'react';
import { motion } from 'framer-motion';
import { FileText, CheckCircle, AlertTriangle, Scale, ArrowLeft, Mail } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useUserStore } from '@/store/userStore';

const TermsOfService: React.FC = () => {
    const { isDark } = useUserStore();

    const sections = [
        {
            icon: CheckCircle,
            title: "Acceptance of Terms",
            content: [
                "By accessing or using DataVision, you agree to be bound by these Terms of Service.",
                "If you disagree with any part of these terms, you may not access the service.",
                "We reserve the right to update these terms at any time. Continued use constitutes acceptance of changes."
            ]
        },
        {
            icon: FileText,
            title: "Description of Service",
            content: [
                "DataVision is an AI-powered Enterprise Analytics Platform that provides:",
                "• Automated data analysis and visualization from uploaded CSV/Excel files",
                "• Machine Learning model training (Fast and Ultra modes) for predictions",
                "• AI-powered chat assistant for data queries and insights",
                "• Automated dashboard generation with KPIs and charts",
                "• Scheduled email reports (daily/weekly) with AI-generated insights"
            ]
        },
        {
            icon: Scale,
            title: "User Responsibilities",
            content: [
                "You are responsible for maintaining the confidentiality of your account credentials.",
                "You agree not to upload malicious, illegal, or copyrighted content without authorization.",
                "You will not attempt to reverse engineer, hack, or disrupt the service.",
                "You are responsible for ensuring you have rights to any data you upload.",
                "You agree to use the service for lawful purposes only."
            ]
        },
        {
            icon: AlertTriangle,
            title: "Limitations & Disclaimers",
            content: [
                "**No Guarantee of Accuracy**: ML predictions and AI insights are for informational purposes. We do not guarantee accuracy of analysis results.",
                "**Service Availability**: We strive for 99% uptime but do not guarantee uninterrupted service.",
                "**Data Processing**: Large files may require additional processing time. Ultra mode training may take 5-10 minutes.",
                "**Free Tier Limits**: Some features may have usage limits under the free tier."
            ]
        }
    ];

    return (
        <div className="min-h-screen" style={{ backgroundColor: 'var(--bg-primary)' }}>
            {/* Header */}
            <header className="border-b" style={{ borderColor: 'var(--border-color)', backgroundColor: 'var(--bg-secondary)' }}>
                <div className="max-w-4xl mx-auto px-6 py-4">
                    <Link to="/" className="inline-flex items-center gap-2 text-sm hover:opacity-80 transition-opacity" style={{ color: 'var(--text-muted)' }}>
                        <ArrowLeft className="w-4 h-4" />
                        Back to Home
                    </Link>
                </div>
            </header>

            {/* Content */}
            <main className="max-w-4xl mx-auto px-6 py-12">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="space-y-8"
                >
                    {/* Title */}
                    <div className="text-center mb-12">
                        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-r from-amber-500 to-orange-500 mb-4">
                            <Scale className="w-8 h-8 text-white" />
                        </div>
                        <h1 className="text-3xl font-bold mb-2" style={{ color: 'var(--text-primary)' }}>Terms of Service</h1>
                        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Last updated: January 2025</p>
                    </div>

                    {/* Introduction */}
                    <div className="p-6 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                        <p style={{ color: 'var(--text-secondary)' }}>
                            Welcome to DataVision! These Terms of Service govern your use of our Enterprise Analytics Platform. Please read them carefully before using our services.
                        </p>
                    </div>

                    {/* Sections */}
                    {sections.map((section, index) => (
                        <motion.div
                            key={index}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.1 }}
                            className="p-6 rounded-2xl border"
                            style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}
                        >
                            <div className="flex items-center gap-3 mb-4">
                                <div className="p-2 rounded-lg bg-amber-500/10">
                                    <section.icon className="w-5 h-5 text-amber-500" />
                                </div>
                                <h2 className="text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>{section.title}</h2>
                            </div>
                            <ul className="space-y-3">
                                {section.content.map((item, i) => (
                                    <li key={i} className="flex items-start gap-2" style={{ color: 'var(--text-secondary)' }}>
                                        {!item.startsWith('•') && <span className="text-amber-500 mt-1.5">•</span>}
                                        <span dangerouslySetInnerHTML={{ __html: item.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />
                                    </li>
                                ))}
                            </ul>
                        </motion.div>
                    ))}

                    {/* Intellectual Property */}
                    <div className="p-6 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                        <h2 className="text-xl font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>Intellectual Property</h2>
                        <ul className="space-y-3" style={{ color: 'var(--text-secondary)' }}>
                            <li className="flex items-start gap-2"><span className="text-amber-500">•</span>DataVision and its features are the property of the developer.</li>
                            <li className="flex items-start gap-2"><span className="text-amber-500">•</span>You retain ownership of all data you upload to the platform.</li>
                            <li className="flex items-start gap-2"><span className="text-amber-500">•</span>ML models trained on your data belong to you.</li>
                            <li className="flex items-start gap-2"><span className="text-amber-500">•</span>We do not claim ownership of insights generated from your data.</li>
                        </ul>
                    </div>

                    {/* Termination */}
                    <div className="p-6 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                        <h2 className="text-xl font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>Account Termination</h2>
                        <ul className="space-y-3" style={{ color: 'var(--text-secondary)' }}>
                            <li className="flex items-start gap-2"><span className="text-amber-500">•</span>You may delete your account at any time through Settings.</li>
                            <li className="flex items-start gap-2"><span className="text-amber-500">•</span>We may suspend accounts that violate these terms.</li>
                            <li className="flex items-start gap-2"><span className="text-amber-500">•</span>Upon termination, your data will be deleted within 30 days.</li>
                        </ul>
                    </div>

                    {/* Contact */}
                    <div className="p-6 rounded-2xl border bg-gradient-to-r from-amber-500/10 to-orange-500/10" style={{ borderColor: 'var(--border-color)' }}>
                        <div className="flex items-center gap-3 mb-3">
                            <Mail className="w-5 h-5 text-amber-500" />
                            <h2 className="text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>Contact</h2>
                        </div>
                        <p style={{ color: 'var(--text-secondary)' }}>
                            For questions about these terms, contact us at:{' '}
                            <a href="mailto:naveenkumarchapala686@gmail.com" className="text-amber-500 hover:underline">
                                naveenkumarchapala686@gmail.com
                            </a>
                        </p>
                        <p className="mt-2 text-sm" style={{ color: 'var(--text-muted)' }}>
                            Developer: Chapala Naveenkumar
                        </p>
                    </div>
                </motion.div>
            </main>
        </div>
    );
};

export default TermsOfService;
