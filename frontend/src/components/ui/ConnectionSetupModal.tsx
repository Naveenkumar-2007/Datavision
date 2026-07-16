import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { X, Database, Server, User, Copy, Check, Zap, Terminal, Loader2 } from 'lucide-react';
import { useToast } from '@/contexts/ToastContext';
import { useUserStore } from '@/store/userStore';
import { api } from '@/services/api';
import { getAuthHeadersSync, getUserIdSync } from '@/utils/userId';

interface Props {
  source: string; // 'PostgreSQL' | 'Snowflake' | 'Kafka'
  onClose: () => void;
  onConnect: (connectionId: string) => void;
}

// Generate the Python script dynamically based on user inputs and connector type
const generateScript = (source: string, pushUrl: string, host: string, dbName: string, tableName: string, username: string): string => {
  const sourceLower = source.toLowerCase();

  if (sourceLower === 'postgresql') {
    return `import psycopg2, requests, time

# Your unique DataVision Cloud Push URL (do NOT share this)
URL = "${pushUrl}"

# Connect to your local PostgreSQL database
conn = psycopg2.connect(
    dbname="${dbName}",
    user="${username}",
    password="YOUR_PASSWORD",  # <-- Enter your password here
    host="${host}",
    port="5432"
)
conn.autocommit = True
cursor = conn.cursor()

print("Connected to ${dbName}! Streaming '${tableName}' to DataVision Cloud...")
previous_count = 0

while True:
    try:
        cursor.execute("SELECT COUNT(*) FROM ${tableName};")
        total_rows = cursor.fetchone()[0]

        rows_per_sec = max(0, total_rows - previous_count) if previous_count > 0 else 0
        previous_count = total_rows

        res = requests.post(URL, json={
            "total_rows": total_rows,
            "rows_per_sec": rows_per_sec,
            "cpu_usage": 0.0,
            "error_rate": 0.0,
            "status": "Streaming ${tableName} to Cloud"
        })
        print(f"Sent: {total_rows} rows -> {res.json()}")
    except Exception as e:
        print("Error:", e)
    time.sleep(1)
`;
  }

  if (sourceLower === 'snowflake') {
    return `import snowflake.connector, requests, time

# Your unique DataVision Cloud Push URL (do NOT share this)
URL = "${pushUrl}"

# Connect to your Snowflake warehouse
conn = snowflake.connector.connect(
    user="${username}",
    password="YOUR_PASSWORD",  # <-- Enter your password here
    account="${host}",         # e.g. xy12345.us-east-1
    warehouse="COMPUTE_WH",
    database="${dbName}",
    schema="PUBLIC"
)
cursor = conn.cursor()

print("Connected to Snowflake! Streaming '${tableName}' to DataVision Cloud...")
previous_count = 0

while True:
    try:
        cursor.execute("SELECT COUNT(*) FROM ${tableName}")
        total_rows = cursor.fetchone()[0]

        rows_per_sec = max(0, total_rows - previous_count) if previous_count > 0 else 0
        previous_count = total_rows

        res = requests.post(URL, json={
            "total_rows": total_rows,
            "rows_per_sec": rows_per_sec,
            "cpu_usage": 0.0,
            "error_rate": 0.0,
            "status": "Streaming ${tableName} from Snowflake"
        })
        print(f"Sent: {total_rows} rows -> {res.json()}")
    except Exception as e:
        print("Error:", e)
    time.sleep(1)
`;
  }

  // Kafka
  return `from confluent_kafka import Consumer
import requests

# Your unique DataVision Cloud Push URL (do NOT share this)
URL = "${pushUrl}"

c = Consumer({
    "bootstrap.servers": "${host}",
    "group.id": "datavision-push-group",
    "auto.offset.reset": "latest"
})
c.subscribe(["${tableName}"])  # Kafka Topic Name

print("Listening to Kafka topic '${tableName}' and streaming to DataVision Cloud...")
total_messages = 0

while True:
    msg = c.poll(1.0)
    if msg is None:
        continue
    if msg.error():
        print("Consumer error:", msg.error())
        continue

    total_messages += 1
    res = requests.post(URL, json={
        "total_rows": total_messages,
        "rows_per_sec": 1,
        "cpu_usage": 0.0,
        "error_rate": 0.0,
        "status": "Receiving Kafka messages"
    })
    print(f"Pushed msg #{total_messages} -> {res.json()}")
`;
};

export const ConnectionSetupModal: React.FC<Props> = ({ source, onClose, onConnect }) => {
  const { isDark } = useUserStore();
  const toast = useToast();

  // Step 1: collect details. Step 2: show generated script. Step 3: launch dashboard.
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [isGenerating, setIsGenerating] = useState(false);
  const [copied, setCopied] = useState(false);

  // Form fields
  const [host, setHost] = useState('');
  const [databaseName, setDatabaseName] = useState('');
  const [targetTable, setTargetTable] = useState('');
  const [username, setUsername] = useState('');

  // Generated values
  const [connectionId, setConnectionId] = useState('');
  const [pushUrl, setPushUrl] = useState('');

  const sourceIcon = source === 'PostgreSQL' ? '🐘' : source === 'Snowflake' ? '❄️' : '⚡';
  const sourceColor = source === 'PostgreSQL' ? 'indigo' : source === 'Snowflake' ? 'blue' : 'yellow';

  const placeholders: Record<string, { host: string; db: string; table: string; user: string }> = {
    PostgreSQL: { host: 'localhost', db: 'streaming_db', table: 'weather_data', user: 'postgres' },
    Snowflake: { host: 'xy12345.us-east-1', db: 'PRODUCTION', table: 'SALES_DATA', user: 'admin' },
    Kafka: { host: 'localhost:9092', db: '(not needed for Kafka)', table: 'my_topic', user: '(optional)' },
  };
  const ph = placeholders[source] || placeholders.PostgreSQL;

  const handleGenerate = async () => {
    if (!host || !targetTable) {
      toast.error('Host and Table/Topic are required.');
      return;
    }

    setIsGenerating(true);
    try {
      const response = await fetch('/api/v1/connections', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeadersSync() },
        body: JSON.stringify({
          source_type: 'api_push',
          host,
          database_name: databaseName || 'push',
          target_table: targetTable,
          credentials: 'none'
        })
      });
      const data = await response.json();
      const connId = data.connection_id;
      setConnectionId(connId);

      // Persist guest connections in localStorage
      if (data.is_guest && data.connection) {
        const stored = JSON.parse(localStorage.getItem('guest_live_connections') || '[]');
        stored.unshift({ ...data.connection, source_type: `api_push_${source.toLowerCase()}` });
        localStorage.setItem('guest_live_connections', JSON.stringify(stored));
      }

      const url = `${window.location.protocol}//${window.location.host}/api/v1/push/${connId}`;
      setPushUrl(url);
      setStep(2);
    } catch (err: any) {
      toast.error('Failed to generate connection: ' + (err?.message || 'Unknown error'));
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCopy = () => {
    const script = generateScript(source, pushUrl, host, databaseName, targetTable, username);
    navigator.clipboard.writeText(script);
    setCopied(true);
    toast.success('Script copied to clipboard!');
    setTimeout(() => setCopied(false), 2000);
  };

  const handleLaunchDashboard = () => {
    setStep(3);
    setTimeout(() => {
      onConnect(connectionId);
    }, 1200);
  };

  const inputClasses = `w-full border rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-${sourceColor}-500/50 focus:border-${sourceColor}-500 transition-all ${isDark ? 'bg-black/40 border-gray-700 text-white placeholder-gray-500' : 'bg-white border-gray-300 text-gray-900 placeholder-gray-400'}`;

  return (
    <div className={`fixed inset-0 z-[60] flex items-center justify-center p-4 backdrop-blur-md ${isDark ? 'bg-black/70' : 'bg-white/40'}`}>
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className={`w-full ${step === 2 ? 'max-w-2xl' : 'max-w-md'} border rounded-2xl overflow-hidden shadow-2xl flex flex-col transition-all ${isDark ? 'bg-[#0a0a0a] border-gray-800' : 'bg-white border-gray-200'}`}
      >
        {/* Header */}
        <div className={`p-4 border-b flex items-center justify-between ${isDark ? 'bg-gradient-to-r from-[#111] to-[#0d0d0d] border-gray-800' : 'bg-gray-50 border-gray-200'}`}>
          <div className="flex items-center gap-3">
            <div className="text-2xl">{sourceIcon}</div>
            <div>
              <h2 className={`font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                {step === 1 ? `Connect ${source}` : step === 2 ? 'Your Streaming Client' : 'Launching...'}
              </h2>
              <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                {step === 1 ? 'Enter your database details below' : step === 2 ? 'Copy this script and run it on your machine' : 'Opening live dashboard...'}
              </p>
            </div>
          </div>
          <button onClick={onClose} className={`p-2 rounded-lg transition-colors ${isDark ? 'hover:bg-white/10 text-gray-400 hover:text-white' : 'hover:bg-gray-200 text-gray-500 hover:text-gray-900'}`}>
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6">
          {/* ─── STEP 1: Collect Details ─── */}
          {step === 1 && (
            <div className="space-y-4">
              <div className="space-y-1.5">
                <label className={`text-sm font-medium flex items-center gap-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                  <Server className="w-4 h-4" /> {source === 'Snowflake' ? 'Account Identifier' : 'Host'}
                </label>
                <input type="text" value={host} onChange={e => setHost(e.target.value)} placeholder={`e.g. ${ph.host}`} className={inputClasses} />
              </div>

              {source !== 'Kafka' && (
                <div className="space-y-1.5">
                  <label className={`text-sm font-medium flex items-center gap-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                    <Database className="w-4 h-4" /> Database Name
                  </label>
                  <input type="text" value={databaseName} onChange={e => setDatabaseName(e.target.value)} placeholder={`e.g. ${ph.db}`} className={inputClasses} />
                </div>
              )}

              <div className="space-y-1.5">
                <label className={`text-sm font-medium flex items-center gap-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                  <Database className="w-4 h-4" /> {source === 'Kafka' ? 'Topic Name' : 'Table Name'}
                </label>
                <input type="text" value={targetTable} onChange={e => setTargetTable(e.target.value)} placeholder={`e.g. ${ph.table}`} className={inputClasses} />
              </div>

              <div className="space-y-1.5">
                <label className={`text-sm font-medium flex items-center gap-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                  <User className="w-4 h-4" /> Username
                </label>
                <input type="text" value={username} onChange={e => setUsername(e.target.value)} placeholder={`e.g. ${ph.user}`} className={inputClasses} />
              </div>

              <div className={`p-3 rounded-lg text-xs ${isDark ? 'bg-yellow-500/10 text-yellow-300 border border-yellow-500/20' : 'bg-yellow-50 text-yellow-700 border border-yellow-200'}`}>
                <strong>How it works:</strong> We generate a Python script with your details pre-filled. You run it on your machine — it reads your database locally and securely streams data to DataVision Cloud. Your credentials never leave your machine.
              </div>

              <button
                onClick={handleGenerate}
                disabled={isGenerating}
                className={`w-full mt-2 bg-${sourceColor}-600 hover:bg-${sourceColor}-700 text-white font-semibold py-3 rounded-xl transition-all flex items-center justify-center gap-2 disabled:opacity-70`}
                style={{ backgroundColor: source === 'PostgreSQL' ? '#4f46e5' : source === 'Snowflake' ? '#3b82f6' : '#eab308' }}
              >
                {isGenerating ? (
                  <><Loader2 className="w-5 h-5 animate-spin" /> Generating Secure Push URL...</>
                ) : (
                  <><Terminal className="w-5 h-5" /> Generate Streaming Client</>
                )}
              </button>
            </div>
          )}

          {/* ─── STEP 2: Show Generated Script ─── */}
          {step === 2 && (
            <div className="space-y-4">
              <div className={`flex items-center justify-between p-3 rounded-lg ${isDark ? 'bg-green-500/10 border border-green-500/20' : 'bg-green-50 border border-green-200'}`}>
                <div className="flex items-center gap-2 text-green-400 text-sm font-semibold">
                  <Check className="w-4 h-4" /> Push URL generated successfully!
                </div>
                <button
                  onClick={handleCopy}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${copied ? 'bg-green-500 text-white' : isDark ? 'bg-white/10 text-white hover:bg-white/20' : 'bg-gray-200 text-gray-800 hover:bg-gray-300'}`}
                >
                  {copied ? <><Check className="w-3.5 h-3.5" /> Copied!</> : <><Copy className="w-3.5 h-3.5" /> Copy Script</>}
                </button>
              </div>

              <div className={`rounded-xl border overflow-hidden ${isDark ? 'border-gray-800' : 'border-gray-200'}`}>
                <div className={`px-4 py-2 text-xs font-mono flex items-center gap-2 ${isDark ? 'bg-[#1a1a1a] text-gray-400 border-b border-gray-800' : 'bg-gray-100 text-gray-600 border-b border-gray-200'}`}>
                  <Terminal className="w-3.5 h-3.5" /> datavision_{source.toLowerCase()}_push.py
                </div>
                <pre className={`text-xs p-4 overflow-x-auto whitespace-pre-wrap max-h-[340px] overflow-y-auto font-mono leading-relaxed ${isDark ? 'bg-[#0d0d0d] text-green-300' : 'bg-gray-50 text-gray-800'}`}>
                  {generateScript(source, pushUrl, host, databaseName, targetTable, username)}
                </pre>
              </div>

              <div className={`text-xs space-y-1 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                <p><strong>Step 1:</strong> Copy the script above.</p>
                <p><strong>Step 2:</strong> Replace <code className="text-yellow-400">YOUR_PASSWORD</code> with your actual password.</p>
                <p><strong>Step 3:</strong> Run <code className="text-blue-400">python datavision_{source.toLowerCase()}_push.py</code> on your machine.</p>
                <p><strong>Step 4:</strong> Click the button below to open your Live Dashboard.</p>
              </div>

              <button
                onClick={handleLaunchDashboard}
                className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3 rounded-xl transition-all flex items-center justify-center gap-2"
              >
                <Zap className="w-5 h-5" /> Launch Live Dashboard
              </button>
            </div>
          )}

          {/* ─── STEP 3: Launching animation ─── */}
          {step === 3 && (
            <div className="flex flex-col items-center justify-center py-10 space-y-4">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="w-20 h-20 bg-green-500/20 rounded-full flex items-center justify-center"
              >
                <Zap className="w-10 h-10 text-green-500" />
              </motion.div>
              <h3 className={`text-xl font-bold text-center ${isDark ? 'text-white' : 'text-gray-900'}`}>Launching Live Dashboard</h3>
              <p className={`text-center text-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                Waiting for data from your {source} streaming client...
              </p>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
};
