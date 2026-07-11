/**
 * Privacy Policy Page - DataVision Enterprise Analytics Platform
 * Last updated: January 2025
 */

import React from 'react';
import { motion } from 'framer-motion';
import { Shield, Database, Lock, Mail, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useUserStore } from '@/store/userStore';

const PrivacyPolicy: React.FC = () => {
    const { isDark } = useUserStore();

    const sections = [
        {
            icon: Database,
            title: "Information We Collect",
            content: [
                "**Account Information**: Email address and authentication data when you create an account.",
                "**Uploaded Data**: CSV and Excel files you upload for analysis. These are stored securely and used only for generating insights.",
                "**Usage Data**: How you interact with the platform to improve our services.",
                "**ML Training Data**: Model configurations and training results generated from your uploaded data."
            ]
        },
        {
            icon: Lock,
            title: "How We Use Your Information",
            content: [
                "To provide AI-powered data analysis and ML predictions on your uploaded files.",
                "To generate automated dashboards, reports, and business insights.",
                "To send scheduled email reports (if you enable this feature).",
                "To improve and optimize our analytics algorithms.",
                "To communicate important updates about the service."
            ]
        },
        {
            icon: Shield,
            title: "Data Storage & Security",
            content: [
                "Your data is stored securely using **PostgreSQL** (for authentication and metadata) and **Hugging Face** infrastructure (for application hosting).",
                "All data transfers are encrypted using industry-standard TLS/SSL protocols.",
                "Your uploaded files are isolated per user account and not shared with other users.",
                "ML models trained on your data are stored privately and accessible only to you."
            ]
        },
        {
            icon: Database,
            title: "Data Retention",
            content: [
                "Your uploaded files are retained as long as your account is active.",
                "You can delete your files at any time through the DataHub interface.",
                "Trained ML models are retained until you delete them or your files.",
                "Upon account deletion, all associated data is permanently removed within 30 days."
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
                        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-r from-green-500 to-emerald-500 mb-4">
                            <Shield className="w-8 h-8 text-white" />
                        </div>
                        <h1 className="text-3xl font-bold mb-2" style={{ color: 'var(--text-primary)' }}>Privacy Policy</h1>
                        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Last updated: January 2025</p>
                    </div>

                    {/* Introduction */}
                    <div className="p-6 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                        <p style={{ color: 'var(--text-secondary)' }}>
                            DataVision ("we", "our", or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, and safeguard your information when you use our Enterprise Analytics Platform.
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
                                <div className="p-2 rounded-lg bg-green-500/10">
                                    <section.icon className="w-5 h-5 text-green-500" />
                                </div>
                                <h2 className="text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>{section.title}</h2>
                            </div>
                            <ul className="space-y-3">
                                {section.content.map((item, i) => (
                                    <li key={i} className="flex items-start gap-2" style={{ color: 'var(--text-secondary)' }}>
                                        <span className="text-green-500 mt-1.5">•</span>
                                        <span dangerouslySetInnerHTML={{ __html: item.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />
                                    </li>
                                ))}
                            </ul>
                        </motion.div>
                    ))}

                    {/* Third Party Services */}
                    <div className="p-6 rounded-2xl border" style={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-color)' }}>
                        <h2 className="text-xl font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>Third-Party Services</h2>
                        <p className="mb-4" style={{ color: 'var(--text-secondary)' }}>We use the following third-party services:</p>
                        <ul className="space-y-2" style={{ color: 'var(--text-secondary)' }}>
                            <li className="flex items-start gap-2"><span className="text-green-500">•</span><strong>PostgreSQL</strong> - Authentication and database services</li>
                            <li className="flex items-start gap-2"><span className="text-green-500">•</span><strong>Hugging Face</strong> - Application hosting infrastructure</li>
                            <li className="flex items-start gap-2"><span className="text-green-500">•</span><strong>Groq</strong> - AI/LLM services for intelligent analysis</li>
                            <li className="flex items-start gap-2"><span className="text-green-500">•</span><strong>Resend</strong> - Email delivery for scheduled reports</li>
                        </ul>
                    </div>

                    {/* Contact */}
                    <div className="p-6 rounded-2xl border bg-gradient-to-r from-green-500/10 to-emerald-500/10" style={{ borderColor: 'var(--border-color)' }}>
                        <div className="flex items-center gap-3 mb-3">
                            <Mail className="w-5 h-5 text-green-500" />
                            <h2 className="text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>Contact Us</h2>
                        </div>
                        <p style={{ color: 'var(--text-secondary)' }}>
                            For privacy-related questions or concerns, contact us at:{' '}
                            <a href="mailto:naveenkumarchapala686@gmail.com" className="text-green-500 hover:underline">
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

export default PrivacyPolicy;
