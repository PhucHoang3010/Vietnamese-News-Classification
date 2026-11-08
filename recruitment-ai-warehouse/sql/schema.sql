-- DDL kho dữ liệu tuyển dụng TalentLens (PostgreSQL 16)
-- Sinh tự động từ app/models.py bằng scripts/export_ddl.py

CREATE TABLE dim_department (
	id SERIAL NOT NULL, 
	code VARCHAR(20) NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (code)
);

CREATE TABLE app_user (
	id SERIAL NOT NULL, 
	username VARCHAR(60) NOT NULL, 
	full_name VARCHAR(120) NOT NULL, 
	email VARCHAR(160), 
	hashed_password VARCHAR(255) NOT NULL, 
	role VARCHAR(20) NOT NULL, 
	department_id INTEGER, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	last_login_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (username), 
	FOREIGN KEY(department_id) REFERENCES dim_department (id)
);

CREATE TABLE dim_source (
	id SERIAL NOT NULL, 
	code VARCHAR(30) NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	channel VARCHAR(40) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (code)
);

CREATE TABLE dim_stage (
	id SERIAL NOT NULL, 
	code VARCHAR(30) NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	stage_order INTEGER NOT NULL, 
	sla_days INTEGER NOT NULL, 
	is_terminal BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (code)
);

CREATE TABLE dim_date (
	date_key INTEGER NOT NULL, 
	full_date DATE NOT NULL, 
	day INTEGER NOT NULL, 
	month INTEGER NOT NULL, 
	quarter INTEGER NOT NULL, 
	year INTEGER NOT NULL, 
	iso_week INTEGER NOT NULL, 
	week_start DATE NOT NULL, 
	day_of_week INTEGER NOT NULL, 
	is_weekend BOOLEAN NOT NULL, 
	PRIMARY KEY (date_key), 
	UNIQUE (full_date)
);

CREATE TABLE dim_position (
	id SERIAL NOT NULL, 
	code VARCHAR(30) NOT NULL, 
	title VARCHAR(160) NOT NULL, 
	department_id INTEGER NOT NULL, 
	level VARCHAR(40), 
	location VARCHAR(80), 
	headcount INTEGER NOT NULL, 
	jd_text TEXT, 
	required_skills JSONB NOT NULL, 
	nice_to_have_skills JSONB NOT NULL, 
	aliases JSONB NOT NULL, 
	hiring_manager_id INTEGER, 
	status VARCHAR(20) NOT NULL, 
	opened_date DATE, 
	PRIMARY KEY (id), 
	UNIQUE (code), 
	FOREIGN KEY(department_id) REFERENCES dim_department (id), 
	FOREIGN KEY(hiring_manager_id) REFERENCES app_user (id)
);

CREATE TABLE dim_candidate (
	id SERIAL NOT NULL, 
	candidate_code VARCHAR(20) NOT NULL, 
	full_name VARCHAR(160) NOT NULL, 
	email VARCHAR(160), 
	phone VARCHAR(20), 
	gender VARCHAR(10), 
	date_of_birth DATE, 
	city VARCHAR(80), 
	years_experience FLOAT, 
	education_level VARCHAR(40), 
	current_title VARCHAR(160), 
	skills JSONB NOT NULL, 
	skill_groups JSONB NOT NULL, 
	cv_text TEXT, 
	cv_file_name VARCHAR(255), 
	first_source_id INTEGER, 
	merged_identities JSONB NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (candidate_code), 
	FOREIGN KEY(first_source_id) REFERENCES dim_source (id)
);
CREATE INDEX ix_dim_candidate_phone ON dim_candidate (phone);
CREATE INDEX ix_dim_candidate_email ON dim_candidate (email);

CREATE TABLE fact_application (
	id SERIAL NOT NULL, 
	application_code VARCHAR(20) NOT NULL, 
	candidate_id INTEGER NOT NULL, 
	position_id INTEGER NOT NULL, 
	source_id INTEGER NOT NULL, 
	applied_date_key INTEGER NOT NULL, 
	applied_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	current_stage_id INTEGER NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	closed_at TIMESTAMP WITHOUT TIME ZONE, 
	rejection_reason TEXT, 
	rejection_category VARCHAR(40), 
	expected_salary FLOAT, 
	source_systems JSONB NOT NULL, 
	external_ids JSONB NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_application_candidate_position UNIQUE (candidate_id, position_id), 
	UNIQUE (application_code), 
	FOREIGN KEY(candidate_id) REFERENCES dim_candidate (id), 
	FOREIGN KEY(position_id) REFERENCES dim_position (id), 
	FOREIGN KEY(source_id) REFERENCES dim_source (id), 
	FOREIGN KEY(applied_date_key) REFERENCES dim_date (date_key), 
	FOREIGN KEY(current_stage_id) REFERENCES dim_stage (id)
);
CREATE INDEX ix_fact_application_candidate_id ON fact_application (candidate_id);
CREATE INDEX ix_fact_application_applied_date_key ON fact_application (applied_date_key);
CREATE INDEX ix_fact_application_source_id ON fact_application (source_id);
CREATE INDEX ix_fact_application_position_id ON fact_application (position_id);

CREATE TABLE fact_stage_event (
	id SERIAL NOT NULL, 
	application_id INTEGER NOT NULL, 
	stage_id INTEGER NOT NULL, 
	entered_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	exited_at TIMESTAMP WITHOUT TIME ZONE, 
	outcome VARCHAR(20) NOT NULL, 
	duration_hours FLOAT, 
	interviewer VARCHAR(120), 
	score FLOAT, 
	feedback TEXT, 
	bias_flags JSONB NOT NULL, 
	source_system VARCHAR(30), 
	PRIMARY KEY (id), 
	CONSTRAINT uq_event_application_stage UNIQUE (application_id, stage_id), 
	FOREIGN KEY(application_id) REFERENCES fact_application (id) ON DELETE CASCADE, 
	FOREIGN KEY(stage_id) REFERENCES dim_stage (id)
);
CREATE INDEX ix_fact_stage_event_stage_id ON fact_stage_event (stage_id);
CREATE INDEX ix_fact_stage_event_application_id ON fact_stage_event (application_id);

CREATE TABLE etl_run (
	id SERIAL NOT NULL, 
	started_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	finished_at TIMESTAMP WITHOUT TIME ZONE, 
	status VARCHAR(20) NOT NULL, 
	triggered_by INTEGER, 
	sources JSONB NOT NULL, 
	stats JSONB NOT NULL, 
	log TEXT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(triggered_by) REFERENCES app_user (id)
);

CREATE TABLE stg_raw_record (
	id SERIAL NOT NULL, 
	etl_run_id INTEGER NOT NULL, 
	source_system VARCHAR(30) NOT NULL, 
	source_file VARCHAR(255) NOT NULL, 
	record_no INTEGER NOT NULL, 
	fingerprint VARCHAR(64) NOT NULL, 
	payload JSONB NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	error TEXT, 
	application_id INTEGER, 
	loaded_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(etl_run_id) REFERENCES etl_run (id) ON DELETE CASCADE, 
	FOREIGN KEY(application_id) REFERENCES fact_application (id) ON DELETE SET NULL
);
CREATE INDEX ix_stg_raw_record_fingerprint ON stg_raw_record (fingerprint);
CREATE INDEX ix_stg_raw_record_etl_run_id ON stg_raw_record (etl_run_id);

CREATE TABLE ai_insight (
	id SERIAL NOT NULL, 
	insight_type VARCHAR(40) NOT NULL, 
	candidate_id INTEGER, 
	application_id INTEGER, 
	position_id INTEGER, 
	content JSONB NOT NULL, 
	provider VARCHAR(20) NOT NULL, 
	model_name VARCHAR(60) NOT NULL, 
	prompt_version VARCHAR(20) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	bias_flags JSONB NOT NULL, 
	removed_fields JSONB NOT NULL, 
	created_by INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	reviewed_by INTEGER, 
	reviewed_at TIMESTAMP WITHOUT TIME ZONE, 
	review_note TEXT, 
	edited BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(candidate_id) REFERENCES dim_candidate (id) ON DELETE CASCADE, 
	FOREIGN KEY(application_id) REFERENCES fact_application (id) ON DELETE CASCADE, 
	FOREIGN KEY(position_id) REFERENCES dim_position (id), 
	FOREIGN KEY(created_by) REFERENCES app_user (id), 
	FOREIGN KEY(reviewed_by) REFERENCES app_user (id)
);

CREATE TABLE weekly_report (
	id SERIAL NOT NULL, 
	week_start DATE NOT NULL, 
	week_end DATE NOT NULL, 
	metrics JSONB NOT NULL, 
	narrative TEXT NOT NULL, 
	provider VARCHAR(20) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	bias_flags JSONB NOT NULL, 
	created_by INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	approved_by INTEGER, 
	approved_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(created_by) REFERENCES app_user (id), 
	FOREIGN KEY(approved_by) REFERENCES app_user (id)
);
CREATE INDEX ix_weekly_report_week_start ON weekly_report (week_start);

CREATE TABLE audit_log (
	id SERIAL NOT NULL, 
	user_id INTEGER, 
	action VARCHAR(60) NOT NULL, 
	entity_type VARCHAR(40), 
	entity_id VARCHAR(40), 
	detail JSONB NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES app_user (id) ON DELETE SET NULL
);
CREATE INDEX ix_audit_log_created_at ON audit_log (created_at);
