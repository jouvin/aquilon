CREATE SEQUENCE service_instance_server_seq;

ALTER TABLE service_instance_server DROP CONSTRAINT sis_host_id_nn;
ALTER TABLE service_instance_server DROP CONSTRAINT service_instance_server_pk;
DROP INDEX service_instance_server_pk;
ALTER TABLE service_instance_server ADD id INTEGER;
UPDATE service_instance_server SET id = service_instance_server_seq.nextval;
ALTER TABLE service_instance_server MODIFY (id CONSTRAINT sis_id_nn NOT NULL);
ALTER TABLE service_instance_server ADD CONSTRAINT service_instance_server_pk PRIMARY KEY (id);
ALTER TABLE service_instance_server ADD cluster_id INTEGER;
ALTER TABLE service_instance_server ADD CONSTRAINT sis_cluster_fk FOREIGN KEY (cluster_id) REFERENCES clstr (id);
ALTER TABLE service_instance_server ADD service_address_id INTEGER;
ALTER TABLE service_instance_server ADD CONSTRAINT sis_srv_addr_fk FOREIGN KEY (service_address_id) REFERENCES service_address (resource_id);
ALTER TABLE service_instance_server ADD address_assignment_id INTEGER;
ALTER TABLE service_instance_server ADD CONSTRAINT sis_addr_assign_fk FOREIGN KEY (address_assignment_id) REFERENCES address_assignment (id);
ALTER TABLE service_instance_server ADD alias_id INTEGER;
ALTER TABLE service_instance_server ADD CONSTRAINT sis_alias_fk FOREIGN KEY (alias_id) REFERENCES alias (dns_record_id);
ALTER TABLE service_instance_server ADD CONSTRAINT service_instance_server_uk UNIQUE (service_instance_id, host_id, cluster_id, address_assignment_id, service_address_id, alias_id);
ALTER TABLE service_instance_server DROP CONSTRAINT sis_si_fk;
ALTER TABLE service_instance_server ADD CONSTRAINT sis_si_fk FOREIGN KEY (service_instance_id) REFERENCES service_instance (id);
ALTER TABLE service_instance_server DROP CONSTRAINT sis_host_fk;
ALTER TABLE service_instance_server ADD CONSTRAINT sis_host_fk FOREIGN KEY (host_id) REFERENCES host (hardware_entity_id);

CREATE INDEX sis_cluster_idx ON service_instance_server (cluster_id);
CREATE INDEX sis_srv_addr_idx ON service_instance_server (service_address_id);
CREATE INDEX sis_addr_assign_idx ON service_instance_server (address_assignment_id);
CREATE INDEX sis_alias_idx ON service_instance_server (alias_id);

QUIT;
