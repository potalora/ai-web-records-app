# Database Implementation Plan for AI Health Records Application

## Executive Summary

This document outlines a comprehensive plan for implementing a HIPAA-compliant database infrastructure for the AI Health Records Application using PostgreSQL, Prisma ORM, and open-source security libraries. The design prioritizes data security, audit trails, encryption, and access controls while maintaining performance and scalability.

## Architecture Overview

### Technology Stack
- **Database**: PostgreSQL 15+ (open source, HIPAA-compliant capable)
- **ORM**: Prisma 5.x (type-safe database access)
- **Encryption**: 
  - `node-forge` or `crypto` (built-in) for application-level encryption
  - PostgreSQL native encryption (TDE) for at-rest encryption
- **Audit Logging**: Custom implementation with `winston` + database triggers
- **Access Control**: Row-Level Security (RLS) with PostgreSQL policies
- **Connection Security**: SSL/TLS with certificate validation

### Database Structure Overview
```
┌─────────────────┐
│   Application   │
└────────┬────────┘
         │ Prisma ORM
         │ + Encryption Middleware
┌────────▼────────┐
│   PostgreSQL    │
│  - Encrypted    │
│  - Audited      │
│  - RLS Enabled  │
└─────────────────┘
```

## Detailed Database Schema

### Core Tables

#### 1. Users Table
```prisma
model User {
  id                String   @id @default(cuid())
  email             String   @unique
  emailVerified     DateTime?
  password          String   // Encrypted with bcrypt
  role              UserRole @default(PATIENT)
  mfaEnabled        Boolean  @default(false)
  mfaSecret         String?  // Encrypted
  lastLogin         DateTime?
  failedLoginCount  Int      @default(0)
  accountLocked     Boolean  @default(false)
  accountLockedAt   DateTime?
  
  // HIPAA Requirements
  termsAcceptedAt   DateTime?
  privacyAcceptedAt DateTime?
  
  // Relationships
  profile           UserProfile?
  auditLogs         AuditLog[]
  healthRecords     HealthRecord[]
  accessLogs        AccessLog[]
  sessions          UserSession[]
  
  // Timestamps
  createdAt         DateTime @default(now())
  updatedAt         DateTime @updatedAt
  deletedAt         DateTime? // Soft delete
  
  @@index([email])
  @@index([deletedAt])
}

enum UserRole {
  PATIENT
  PROVIDER
  ADMIN
  SYSTEM
}
```

#### 2. User Profile (PII Separation)
```prisma
model UserProfile {
  id              String   @id @default(cuid())
  userId          String   @unique
  user            User     @relation(fields: [userId], references: [id])
  
  // Encrypted PII fields
  firstName       String   // Encrypted
  lastName        String   // Encrypted
  dateOfBirth     String   // Encrypted
  ssn             String?  // Encrypted + masked
  phone           String?  // Encrypted
  
  // Address (consider separate table for normalization)
  addressLine1    String?  // Encrypted
  addressLine2    String?  // Encrypted
  city            String?  // Encrypted
  state           String?
  zipCode         String?  // Encrypted
  country         String?
  
  // Emergency Contact
  emergencyName   String?  // Encrypted
  emergencyPhone  String?  // Encrypted
  emergencyRel    String?
  
  createdAt       DateTime @default(now())
  updatedAt       DateTime @updatedAt
  
  @@index([userId])
}
```

#### 3. Health Records
```prisma
model HealthRecord {
  id              String   @id @default(cuid())
  userId          String
  user            User     @relation(fields: [userId], references: [id])
  
  recordType      RecordType
  sourceSystem    String?
  externalId      String?  // ID from source system
  
  // Metadata
  recordDate      DateTime
  title           String
  description     String?
  
  // Encrypted content
  encryptedData   Bytes    // Full record data encrypted
  encryptionIv    String   // Initialization vector
  encryptionAlg   String   @default("AES-256-GCM")
  
  // Processing status
  status          ProcessingStatus @default(PENDING)
  processingError String?
  
  // Relationships
  documents       Document[]
  fhirResources   FhirResource[]
  summaries       Summary[]
  accessLogs      AccessLog[]
  
  // Timestamps
  createdAt       DateTime @default(now())
  updatedAt       DateTime @updatedAt
  deletedAt       DateTime? // Soft delete
  
  @@index([userId, recordDate])
  @@index([status])
  @@index([deletedAt])
}

enum RecordType {
  LAB_RESULT
  IMAGING
  CLINICAL_NOTE
  PRESCRIPTION
  IMMUNIZATION
  PROCEDURE
  DIAGNOSIS
  VITAL_SIGNS
  OTHER
}

enum ProcessingStatus {
  PENDING
  PROCESSING
  COMPLETED
  FAILED
  ARCHIVED
}
```

#### 4. Documents (File Storage Reference)
```prisma
model Document {
  id              String   @id @default(cuid())
  healthRecordId  String
  healthRecord    HealthRecord @relation(fields: [healthRecordId], references: [id])
  
  fileName        String
  fileType        String
  mimeType        String
  fileSize        Int
  
  // Storage location (encrypted path)
  storageUrl      String   // Encrypted S3/local path
  checksumSha256  String   // File integrity
  
  // Encryption details
  encrypted       Boolean  @default(true)
  encryptionKey   String?  // Encrypted key reference
  
  // Processing
  status          ProcessingStatus @default(PENDING)
  extractedText   String?  // Encrypted
  
  // Metadata
  uploadedBy      String
  uploadedAt      DateTime @default(now())
  processedAt     DateTime?
  
  createdAt       DateTime @default(now())
  updatedAt       DateTime @updatedAt
  deletedAt       DateTime? // Soft delete
  
  @@index([healthRecordId])
  @@index([status])
}
```

#### 5. FHIR Resources
```prisma
model FhirResource {
  id              String   @id @default(cuid())
  healthRecordId  String?
  healthRecord    HealthRecord? @relation(fields: [healthRecordId], references: [id])
  
  resourceType    String   // Bundle, Patient, Observation, etc.
  fhirId          String   // FHIR resource ID
  fhirVersion     String   @default("4.0.1")
  
  // Encrypted FHIR JSON
  resourceData    Bytes    // Encrypted JSON
  encryptionIv    String
  
  // Indexable fields for search (not encrypted)
  patientRef      String?
  encounterRef    String?
  dateRecorded    DateTime?
  
  // Metadata
  sourceSystem    String?
  importedAt      DateTime @default(now())
  
  createdAt       DateTime @default(now())
  updatedAt       DateTime @updatedAt
  
  @@unique([resourceType, fhirId])
  @@index([patientRef])
  @@index([dateRecorded])
}
```

#### 6. AI Summaries
```prisma
model Summary {
  id              String   @id @default(cuid())
  healthRecordId  String
  healthRecord    HealthRecord @relation(fields: [healthRecordId], references: [id])
  
  summaryType     SummaryType
  llmProvider     String   // openai, google, anthropic
  llmModel        String   // gpt-4, gemini-pro, claude-3
  
  // Encrypted content
  summaryText     Bytes    // Encrypted
  encryptionIv    String
  
  // Metadata
  confidence      Float?
  processingTime  Int      // milliseconds
  tokenCount      Int?
  
  createdAt       DateTime @default(now())
  
  @@index([healthRecordId])
  @@index([summaryType])
}

enum SummaryType {
  GENERAL
  DIAGNOSTIC
  TREATMENT
  MEDICATION
  LAB_INTERPRETATION
}
```

#### 7. Audit Logs (HIPAA Required)
```prisma
model AuditLog {
  id              String   @id @default(cuid())
  userId          String?
  user            User?    @relation(fields: [userId], references: [id])
  
  action          AuditAction
  resourceType    String
  resourceId      String
  
  // Request details
  ipAddress       String
  userAgent       String?
  requestMethod   String?
  requestPath     String?
  
  // Change tracking
  oldValues       Json?    // Encrypted
  newValues       Json?    // Encrypted
  
  // Result
  success         Boolean
  errorMessage    String?
  
  timestamp       DateTime @default(now())
  
  @@index([userId, timestamp])
  @@index([resourceType, resourceId])
  @@index([timestamp])
}

enum AuditAction {
  CREATE
  READ
  UPDATE
  DELETE
  LOGIN
  LOGOUT
  EXPORT
  PRINT
  SHARE
  DENY_ACCESS
}
```

#### 8. Access Logs (Track all PHI access)
```prisma
model AccessLog {
  id              String   @id @default(cuid())
  userId          String
  user            User     @relation(fields: [userId], references: [id])
  
  healthRecordId  String
  healthRecord    HealthRecord @relation(fields: [healthRecordId], references: [id])
  
  accessType      AccessType
  purpose         String   // Reason for access
  
  // Context
  ipAddress       String
  sessionId       String?
  
  accessedAt      DateTime @default(now())
  
  @@index([userId, accessedAt])
  @@index([healthRecordId, accessedAt])
}

enum AccessType {
  VIEW
  DOWNLOAD
  PRINT
  SHARE
  API_ACCESS
}
```

#### 9. User Sessions
```prisma
model UserSession {
  id              String   @id @default(cuid())
  userId          String
  user            User     @relation(fields: [userId], references: [id])
  
  sessionToken    String   @unique
  ipAddress       String
  userAgent       String
  
  createdAt       DateTime @default(now())
  expiresAt       DateTime
  lastActivity    DateTime @default(now())
  
  @@index([sessionToken])
  @@index([userId])
  @@index([expiresAt])
}
```

#### 10. Encryption Keys (Key Rotation)
```prisma
model EncryptionKey {
  id              String   @id @default(cuid())
  keyName         String   @unique
  keyVersion      Int
  
  // Encrypted with master key
  encryptedKey    String
  algorithm       String   @default("AES-256-GCM")
  
  // Usage tracking
  purpose         String   // user_data, health_records, etc.
  
  activeFrom      DateTime @default(now())
  activeTo        DateTime?
  
  createdAt       DateTime @default(now())
  rotatedAt       DateTime?
  
  @@index([keyName, keyVersion])
  @@index([activeFrom, activeTo])
}
```

## Security Implementation

### 1. Encryption Strategy

#### Application-Level Encryption
```typescript
// encryption.service.ts
import * as crypto from 'crypto';

class EncryptionService {
  private algorithm = 'aes-256-gcm';
  
  async encryptField(plaintext: string, key: Buffer): Promise<{
    encrypted: Buffer,
    iv: string,
    authTag: string
  }> {
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipheriv(this.algorithm, key, iv);
    
    const encrypted = Buffer.concat([
      cipher.update(plaintext, 'utf8'),
      cipher.final()
    ]);
    
    const authTag = cipher.getAuthTag();
    
    return {
      encrypted,
      iv: iv.toString('base64'),
      authTag: authTag.toString('base64')
    };
  }
  
  async decryptField(
    encrypted: Buffer,
    key: Buffer,
    iv: string,
    authTag: string
  ): Promise<string> {
    const decipher = crypto.createDecipheriv(
      this.algorithm,
      key,
      Buffer.from(iv, 'base64')
    );
    
    decipher.setAuthTag(Buffer.from(authTag, 'base64'));
    
    const decrypted = Buffer.concat([
      decipher.update(encrypted),
      decipher.final()
    ]);
    
    return decrypted.toString('utf8');
  }
}
```

#### Prisma Middleware for Automatic Encryption
```typescript
// prisma.middleware.ts
const encryptedFields = {
  UserProfile: ['firstName', 'lastName', 'dateOfBirth', 'ssn', 'phone'],
  HealthRecord: ['encryptedData'],
  Summary: ['summaryText']
};

prisma.$use(async (params, next) => {
  // Encrypt on create/update
  if (params.action === 'create' || params.action === 'update') {
    if (encryptedFields[params.model]) {
      for (const field of encryptedFields[params.model]) {
        if (params.args.data[field]) {
          const encrypted = await encryptionService.encryptField(
            params.args.data[field],
            await getEncryptionKey(params.model)
          );
          params.args.data[field] = encrypted.encrypted;
          params.args.data[`${field}Iv`] = encrypted.iv;
        }
      }
    }
  }
  
  const result = await next(params);
  
  // Decrypt on read
  if (params.action === 'findUnique' || params.action === 'findFirst') {
    if (result && encryptedFields[params.model]) {
      for (const field of encryptedFields[params.model]) {
        if (result[field]) {
          result[field] = await encryptionService.decryptField(
            result[field],
            await getEncryptionKey(params.model),
            result[`${field}Iv`]
          );
        }
      }
    }
  }
  
  return result;
});
```

### 2. Database-Level Security

#### PostgreSQL Configuration
```sql
-- Enable encryption at rest
ALTER SYSTEM SET ssl = on;
ALTER SYSTEM SET ssl_cert_file = 'server.crt';
ALTER SYSTEM SET ssl_key_file = 'server.key';

-- Enable row-level security
ALTER TABLE health_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE fhir_resources ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY health_records_isolation ON health_records
  FOR ALL
  USING (user_id = current_setting('app.current_user_id')::TEXT);

-- Audit trigger
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS trigger AS $$
BEGIN
  INSERT INTO audit_logs (
    user_id,
    action,
    resource_type,
    resource_id,
    old_values,
    new_values,
    timestamp
  ) VALUES (
    current_setting('app.current_user_id')::TEXT,
    TG_OP,
    TG_TABLE_NAME,
    NEW.id,
    to_jsonb(OLD),
    to_jsonb(NEW),
    NOW()
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply audit triggers
CREATE TRIGGER audit_health_records
  AFTER INSERT OR UPDATE OR DELETE ON health_records
  FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
```

### 3. Access Control Implementation

#### Role-Based Access Control (RBAC)
```typescript
// access-control.service.ts
interface AccessPolicy {
  resource: string;
  actions: string[];
  condition?: (user: User, resource: any) => boolean;
}

const policies: Record<UserRole, AccessPolicy[]> = {
  PATIENT: [
    {
      resource: 'HealthRecord',
      actions: ['read'],
      condition: (user, record) => record.userId === user.id
    },
    {
      resource: 'Summary',
      actions: ['read'],
      condition: (user, summary) => {
        // Check if user owns the related health record
        return summary.healthRecord.userId === user.id;
      }
    }
  ],
  PROVIDER: [
    {
      resource: 'HealthRecord',
      actions: ['read', 'create', 'update'],
      condition: (user, record) => {
        // Check if provider has consent to access
        return hasPatientConsent(user.id, record.userId);
      }
    }
  ],
  ADMIN: [
    {
      resource: 'AuditLog',
      actions: ['read'],
      condition: () => true // Admins can read all audit logs
    }
  ]
};
```

### 4. Session Management

```typescript
// session.service.ts
class SessionService {
  private sessionTimeout = 30 * 60 * 1000; // 30 minutes
  
  async createSession(userId: string, ipAddress: string, userAgent: string) {
    const sessionToken = crypto.randomBytes(32).toString('hex');
    
    const session = await prisma.userSession.create({
      data: {
        userId,
        sessionToken: await hashToken(sessionToken),
        ipAddress,
        userAgent,
        expiresAt: new Date(Date.now() + this.sessionTimeout)
      }
    });
    
    // Log the login
    await prisma.auditLog.create({
      data: {
        userId,
        action: 'LOGIN',
        resourceType: 'UserSession',
        resourceId: session.id,
        ipAddress,
        userAgent,
        success: true
      }
    });
    
    return sessionToken;
  }
  
  async validateSession(sessionToken: string) {
    const hashedToken = await hashToken(sessionToken);
    
    const session = await prisma.userSession.findFirst({
      where: {
        sessionToken: hashedToken,
        expiresAt: { gt: new Date() }
      },
      include: { user: true }
    });
    
    if (!session) {
      throw new UnauthorizedError('Invalid or expired session');
    }
    
    // Update last activity
    await prisma.userSession.update({
      where: { id: session.id },
      data: { lastActivity: new Date() }
    });
    
    return session.user;
  }
}
```

## Implementation Phases

### Phase 1: Foundation (Week 1)
1. **PostgreSQL Setup**
   - Install PostgreSQL 15+
   - Configure SSL/TLS
   - Set up database encryption at rest
   - Create database and user with limited privileges

2. **Prisma Integration**
   - Install Prisma and dependencies
   - Create initial schema
   - Set up migrations
   - Implement connection pooling

3. **Basic Models**
   - User and UserProfile
   - AuditLog
   - UserSession

### Phase 2: Security Layer (Week 2)
1. **Encryption Service**
   - Implement field-level encryption
   - Create key management system
   - Set up Prisma middleware

2. **Authentication**
   - Password hashing (bcrypt)
   - Session management
   - MFA support structure

3. **Audit System**
   - Database triggers
   - Application-level logging
   - Access tracking

### Phase 3: Health Data Models (Week 3)
1. **Core Health Models**
   - HealthRecord
   - Document
   - FhirResource
   - Summary

2. **Access Control**
   - Row-level security policies
   - RBAC implementation
   - Consent management

3. **Data Import/Export**
   - FHIR resource handling
   - Document storage integration
   - Bulk import capabilities

### Phase 4: Testing & Compliance (Week 4)
1. **Security Testing**
   - Penetration testing
   - Encryption verification
   - Access control testing

2. **Performance Testing**
   - Query optimization
   - Index tuning
   - Load testing

3. **Compliance Verification**
   - HIPAA checklist review
   - Audit trail testing
   - Data retention policies

## Environment Configuration

### Development Environment
```env
# .env.development
DATABASE_URL="postgresql://healthapp:dev_password@localhost:5432/health_records_dev?schema=public&sslmode=require"
DIRECT_URL="postgresql://healthapp:dev_password@localhost:5432/health_records_dev?schema=public&sslmode=require"

# Encryption
MASTER_KEY_FILE="./keys/master.key"
ENCRYPTION_ALGORITHM="aes-256-gcm"

# Session
SESSION_SECRET="development_secret_change_in_production"
SESSION_TIMEOUT_MINUTES="30"

# Audit
AUDIT_LOG_LEVEL="debug"
ENABLE_QUERY_LOGGING="true"
```

### Production Environment
```env
# .env.production
DATABASE_URL="postgresql://healthapp:${DB_PASSWORD}@${DB_HOST}:5432/health_records_prod?schema=public&sslmode=require&sslcert=${SSL_CERT}&sslkey=${SSL_KEY}"

# Encryption (use key management service in production)
KMS_KEY_ID="${AWS_KMS_KEY_ID}"
ENCRYPTION_ALGORITHM="aes-256-gcm"

# Session
SESSION_SECRET="${SESSION_SECRET}"
SESSION_TIMEOUT_MINUTES="15"
FORCE_HTTPS="true"

# Audit
AUDIT_LOG_LEVEL="info"
ENABLE_QUERY_LOGGING="false"
AUDIT_RETENTION_DAYS="2555" # 7 years per HIPAA
```

## Monitoring & Maintenance

### Database Monitoring
```typescript
// monitoring.service.ts
class DatabaseMonitor {
  async checkHealth() {
    const checks = {
      connection: await this.checkConnection(),
      encryption: await this.checkEncryption(),
      auditLog: await this.checkAuditLog(),
      performance: await this.checkPerformance()
    };
    
    return checks;
  }
  
  async checkConnection() {
    try {
      await prisma.$queryRaw`SELECT 1`;
      return { status: 'healthy', latency: Date.now() - start };
    } catch (error) {
      return { status: 'unhealthy', error: error.message };
    }
  }
  
  async checkEncryption() {
    // Verify encryption keys are accessible
    const keys = await prisma.encryptionKey.findMany({
      where: {
        activeFrom: { lte: new Date() },
        OR: [
          { activeTo: null },
          { activeTo: { gte: new Date() } }
        ]
      }
    });
    
    return { 
      status: keys.length > 0 ? 'healthy' : 'unhealthy',
      activeKeys: keys.length 
    };
  }
}
```

### Backup Strategy
```bash
#!/bin/bash
# backup.sh

# Encrypted backup
pg_dump $DATABASE_URL | \
  openssl enc -aes-256-cbc -salt -k $BACKUP_PASSWORD | \
  aws s3 cp - s3://$BACKUP_BUCKET/health-records-$(date +%Y%m%d-%H%M%S).sql.enc

# Verify backup
if [ $? -eq 0 ]; then
  echo "Backup successful"
  # Log to audit
else
  echo "Backup failed"
  # Alert administrators
fi
```

### Key Rotation
```typescript
// key-rotation.service.ts
class KeyRotationService {
  async rotateKeys() {
    // Generate new key
    const newKey = crypto.randomBytes(32);
    
    // Start transaction
    await prisma.$transaction(async (tx) => {
      // Create new key record
      const newKeyRecord = await tx.encryptionKey.create({
        data: {
          keyName: 'health_records',
          keyVersion: await this.getNextVersion(),
          encryptedKey: await this.encryptWithMasterKey(newKey),
          purpose: 'health_records'
        }
      });
      
      // Re-encrypt existing data
      const records = await tx.healthRecord.findMany();
      
      for (const record of records) {
        // Decrypt with old key
        const decrypted = await this.decrypt(record.encryptedData);
        
        // Encrypt with new key
        const encrypted = await this.encrypt(decrypted, newKey);
        
        await tx.healthRecord.update({
          where: { id: record.id },
          data: {
            encryptedData: encrypted.data,
            encryptionIv: encrypted.iv
          }
        });
      }
      
      // Mark old key as rotated
      await tx.encryptionKey.updateMany({
        where: {
          keyName: 'health_records',
          keyVersion: { lt: newKeyRecord.keyVersion }
        },
        data: {
          activeTo: new Date(),
          rotatedAt: new Date()
        }
      });
    });
  }
}
```

## Compliance Checklist

### HIPAA Technical Safeguards
- [ ] Access Control (164.312(a)(1))
  - [ ] Unique user identification
  - [ ] Automatic logoff
  - [ ] Encryption and decryption
- [ ] Audit Controls (164.312(b))
  - [ ] Hardware, software, procedural mechanisms
  - [ ] Record and examine activity
- [ ] Integrity (164.312(c)(1))
  - [ ] Electronic PHI not improperly altered/destroyed
  - [ ] Checksums for file integrity
- [ ] Transmission Security (164.312(e)(1))
  - [ ] Guard against unauthorized access during transmission
  - [ ] Encryption of data in transit

### HIPAA Administrative Safeguards
- [ ] Security Officer designation
- [ ] Workforce training records
- [ ] Access management procedures
- [ ] Security incident procedures
- [ ] Contingency plan (backup, disaster recovery)
- [ ] Regular security assessments

### Additional Security Measures
- [ ] Regular penetration testing
- [ ] Vulnerability scanning
- [ ] Security patch management
- [ ] Intrusion detection system
- [ ] Data loss prevention (DLP)
- [ ] Security information and event management (SIEM)

## Risk Mitigation Strategies

### 1. Data Breach Prevention
- Implement rate limiting on all endpoints
- Use Web Application Firewall (WAF)
- Regular security audits
- Employee security training
- Principle of least privilege

### 2. High Availability
- Database replication (primary/replica)
- Automated failover
- Regular backup testing
- Disaster recovery plan
- Geographic redundancy

### 3. Performance Optimization
- Implement caching layer (Redis)
- Database query optimization
- Connection pooling
- Lazy loading of encrypted fields
- Archival of old records

## Cost Considerations

### Open Source Stack (Monthly Estimate)
- PostgreSQL: $0 (self-hosted) or ~$100-500 (managed)
- Prisma: $0 (open source)
- Encryption libraries: $0
- Monitoring (Prometheus/Grafana): $0
- Backup storage: ~$50-200
- SSL certificates: $0 (Let's Encrypt)

### Commercial Alternatives
- AWS RDS with encryption: ~$200-1000/month
- Azure Database for PostgreSQL: ~$150-800/month
- Google Cloud SQL: ~$100-700/month

## Conclusion

This implementation plan provides a comprehensive approach to building a HIPAA-compliant database infrastructure using open-source technologies. The design prioritizes security through multiple layers of protection including encryption, access controls, audit logging, and monitoring while maintaining performance and scalability.

Key success factors:
1. Consistent implementation of encryption across all PHI
2. Comprehensive audit logging without performance impact
3. Regular security assessments and updates
4. Clear separation of concerns between application and database security
5. Automated monitoring and alerting for compliance violations

Next steps after approval:
1. Set up development environment
2. Implement Phase 1 foundation
3. Create integration tests for security features
4. Document all security procedures
5. Schedule security assessment before production deployment