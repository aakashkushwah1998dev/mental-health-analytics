-- =============================================================
-- Supabase SQL (paste into Supabase SQL editor)
-- Fixes the Streamlit questionnaire "ON CONFLICT" requirement by
-- ensuring a UNIQUE constraint exists for (attempt_id, category_id).
--
-- Safe to run multiple times (idempotent).
-- =============================================================

-- 1) Ensure attempt_id columns exist (older schemas may not have them).
ALTER TABLE responses ADD COLUMN IF NOT EXISTS attempt_id INT;
ALTER TABLE scores ADD COLUMN IF NOT EXISTS attempt_id INT;

-- 2) Ensure questions reverse-scoring flag exists.
ALTER TABLE questions ADD COLUMN IF NOT EXISTS is_reversed BOOLEAN DEFAULT FALSE;

-- 3) Ensure the unique constraint exists for score upserts.
ALTER TABLE scores
DROP CONSTRAINT IF EXISTS scores_attempt_id_category_id_key;

ALTER TABLE scores
ADD CONSTRAINT scores_attempt_id_category_id_key UNIQUE (attempt_id, category_id);

-- Optional: create helpful index for reads
CREATE INDEX IF NOT EXISTS idx_scores_user_attempt
ON scores (user_id, attempt_id);
