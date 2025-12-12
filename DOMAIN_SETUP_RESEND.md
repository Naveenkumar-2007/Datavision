# Domain Setup for ai20insights.tech in Resend

## Step 1: Add Domain to Resend

1. **Go to Resend Dashboard**: https://resend.com/domains
2. **Click "Add Domain"**
3. **Enter**: `ai20insights.tech`
4. **Click "Add Domain"**

---

## Step 2: Add DNS Records

Resend will show you DNS records to add. You need to add these to your domain registrar (GoDaddy, Namecheap, Cloudflare, etc.)

### Records You'll Need to Add:

**1. SPF Record (TXT)**
```
Type: TXT
Name: @
Value: v=spf1 include:amazonses.com ~all
```

**2. DKIM Records (3 CNAME records)**
```
Type: CNAME
Name: resend._domainkey
Value: [Resend will provide this]

Type: CNAME  
Name: resend1._domainkey
Value: [Resend will provide this]

Type: CNAME
Name: resend2._domainkey
Value: [Resend will provide this]
```

**3. DMARC Record (TXT)**
```
Type: TXT
Name: _dmarc
Value: v=DMARC1; p=none; rua=mailto:dmarc@ai20insights.tech
```

---

## Step 3: Verify Domain

1. After adding DNS records, wait 5-10 minutes
2. Go back to Resend dashboard
3. Click **"Verify Domain"**
4. ✅ Domain status should change to "Verified"

---

## Step 4: Test Email

Once verified, run this command:

```bash
Invoke-WebRequest -Uri http://localhost:8000/test-email -Method POST
```

**Expected Result**: 
- ✅ Email sent from `insights@ai20insights.tech`
- ✅ Lands in **INBOX** (not spam!)
- ✅ Professional sender name: "AI Business Analyst"
- ✅ All links work correctly

---

## Alternative Email Addresses You Can Use:

Once domain is verified, you can use any email @ai20insights.tech:

- `insights@ai20insights.tech` ✅ (currently set)
- `notifications@ai20insights.tech`
- `alerts@ai20insights.tech`
- `ai@ai20insights.tech`
- `noreply@ai20insights.tech`

---

## Where to Add DNS Records:

### If using **GoDaddy**:
1. Go to GoDaddy DNS Management
2. Find "ai20insights.tech"
3. Click "Manage DNS"
4. Add the records shown by Resend

### If using **Cloudflare**:
1. Go to Cloudflare dashboard
2. Select "ai20insights.tech"
3. Go to "DNS" tab
4. Add the records

### If using **Namecheap**:
1. Go to Domain List
2. Click "Manage" for ai20insights.tech
3. Advanced DNS tab
4. Add the records

---

## Verification Timeline:

- **DNS propagation**: 5-30 minutes (usually fast)
- **Resend verification**: Instant after DNS propagates
- **Total time**: ~10-15 minutes

---

## Benefits After Verification:

✅ **No more spam** - Emails land in inbox  
✅ **Professional sender** - "insights@ai20insights.tech"  
✅ **Better deliverability** - Proper SPF/DKIM/DMARC  
✅ **Brand trust** - Your own domain  
✅ **No "dangerous link" warnings**  

---

## Current Status:

- ✅ Email service updated to use `insights@ai20insights.tech`
- ⏳ **Next**: Add domain to Resend and verify DNS records
- ⏳ **Then**: Test email will work perfectly!

---

**Let me know when you've added the domain to Resend, and I'll help you test it!**
