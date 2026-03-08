import Imap from 'imap';
import { simpleParser } from 'mailparser';

// CONFIG
const EMAIL = 'decencyawowo7@gmail.com';
const PASS  = 'ixyizkdpbwyphbsz';

// COMMAND LINE TARGET
const args = process.argv.slice(2);
const flagIndex = args.indexOf('-f');
if (flagIndex === -1 || !args[flagIndex + 1]) {
    console.error('❌ Usage: node gmail_extract_code_fixed.js -f <target_email>');
    process.exit(1);
}
const TARGET_EMAIL = args[flagIndex + 1].toLowerCase();

// IMAP SETUP
const imap = new Imap({
    user: EMAIL,
    password: PASS,
    host: 'imap.gmail.com',
    port: 993,
    tls: true,
    tlsOptions: { rejectUnauthorized: false }
});

function openInbox(cb) {
    imap.openBox('INBOX', false, cb); // read-write
}

function extractCode(text) {
    const match = text.match(/\b\d{6}\b/);
    return match ? match[0] : null;
}

function fetchLatest(n = 50) {
    imap.search(['ALL'], (err, results) => {
        if (err) {
            console.error('Search error:', err);
            process.exit(1);
        }

        if (!results || results.length === 0) {
            console.log('ℹ️ No messages found.');
            process.exit(0);
        }

        const latest = results.reverse().slice(0, n);
        const f = imap.fetch(latest, { bodies: '', struct: true });

        let found = false;
        let totalParsed = 0;

        f.on('message', msg => {
            msg.on('body', stream => {
                simpleParser(stream, (err, parsed) => {
                    totalParsed++;
                    if (err) return;

                    const toText = parsed.to?.text?.toLowerCase() || '';
                    if (toText.includes(TARGET_EMAIL) && !found) {
                        const code = extractCode(parsed.text || '');
                        if (code) {
                            console.log(code); // ✅ log code
                            found = true;
                            imap.end(); // immediately close connection
                        }
                    }

                    // If all messages parsed and nothing found
                    if (totalParsed === latest.length && !found) {
                        console.log('ℹ️ No matching email found.');
                        imap.end();
                    }
                });
            });
        });
    });
}

imap.once('ready', () => {
    openInbox(err => {
        if (err) throw err;
        fetchLatest(50);
    });
});

imap.once('error', err => console.error('IMAP error:', err));
imap.once('end', () => process.exit(0));

imap.connect();
