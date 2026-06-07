-- Message sender role migration for HR-003.
--
-- Existing rows used role='user'. The React transcript contract now uses
-- patient/assistant/system/doctor so future AI and doctor messages can share
-- one table without another role-shape migration.

UPDATE chat_messages
SET role = 'patient'
WHERE role = 'user';

DO $$
DECLARE
    constraint_name TEXT;
BEGIN
    SELECT conname
    INTO constraint_name
    FROM pg_constraint
    WHERE conrelid = 'chat_messages'::regclass
      AND contype = 'c'
      AND pg_get_constraintdef(oid) LIKE '%role%'
      AND pg_get_constraintdef(oid) LIKE '%assistant%'
      AND pg_get_constraintdef(oid) LIKE '%system%'
    LIMIT 1;

    IF constraint_name IS NOT NULL THEN
        EXECUTE format('ALTER TABLE chat_messages DROP CONSTRAINT %I', constraint_name);
    END IF;
END $$;

ALTER TABLE chat_messages
ADD CONSTRAINT chat_messages_role_check
CHECK (role IN ('patient', 'assistant', 'system', 'doctor'));

COMMENT ON COLUMN chat_messages.role IS
'Transcript sender type. Public patient API creates only patient messages in HR-003.';
