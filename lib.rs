use candid::{Principal, CandidType, Deserialize};
use ic_cdk::{init, query, update};
use std::collections::HashMap;
use std::cell::RefCell;

// Vehicle structure
#[derive(Clone, Debug, CandidType, Deserialize)]
struct Vehicle {
    plate: String,
    is_authorized: bool,
}

// Canister persistent state
thread_local! {
    static OWNER: RefCell<Principal> = RefCell::new(Principal::anonymous());
    static VEHICLES: RefCell<HashMap<String, Vehicle>> = RefCell::new(HashMap::new());
}

// Initialize canister with owner
#[init]
fn init(owner: String) {
    OWNER.with(|o| {
        *o.borrow_mut() = Principal::from_text(&owner).expect("Invalid principal format");
    });
}

// Owner-only access control
fn only_owner() -> Result<(), String> {
    OWNER.with(|owner| {
        if ic_cdk::caller() != *owner.borrow() {
            Err("Only owner can call this function".to_string())
        } else {
            Ok(())
        }
    })
}

// Register/update vehicle authorization
#[update]
fn set_vehicle_authorization(plate: String, authorized: bool) -> Result<(), String> {
    only_owner()?;
    
    let normalized = normalize_plate(&plate);
    VEHICLES.with(|v| {
        v.borrow_mut().insert(normalized, Vehicle { plate, is_authorized: authorized });
    });
    Ok(())
}

// Remove vehicle authorization
#[update]
fn remove_vehicle(plate: String) -> Result<(), String> {
    only_owner()?;
    
    let normalized = normalize_plate(&plate);
    VEHICLES.with(|v| {
        v.borrow_mut().remove(&normalized);
    });
    Ok(())
}

// Check authorization status
#[update]
fn check_authorization(plate: String, ipfs_hash: String) -> Result<bool, String> {
    let normalized = normalize_plate(&plate);
    let caller = ic_cdk::caller();
    let timestamp = ic_cdk::api::time();
    
    VEHICLES.with(|v| {
        match v.borrow().get(&normalized) {
            Some(vehicle) if vehicle.is_authorized => {
                log_access("Granted", &plate, caller, timestamp, &ipfs_hash);
                Ok(true)
            }
            Some(_) => {
                log_access("Denied", &plate, caller, timestamp, &ipfs_hash);
                Ok(false)
            }
            None => {
                log_access("NotFound", &plate, caller, timestamp, &ipfs_hash);
                Ok(false)
            }
        }
    })
}

// Get authorization status (query)
#[query]
fn get_authorization_status(plate: String) -> Result<bool, String> {
    let normalized = normalize_plate(&plate);
    VEHICLES.with(|v| {
        v.borrow()
            .get(&normalized)
            .map(|v| v.is_authorized)
            .ok_or("Vehicle not found".to_string())
    })
}

// Helper: Normalize plate number (case-insensitive)
fn normalize_plate(plate: &str) -> String {
    plate.to_lowercase()
}

// Helper: Log access events
fn log_access(status: &str, plate: &str, caller: Principal, timestamp: u64, ipfs_hash: &str) {
    ic_cdk::api::print(format!(
        "Access{}: plate={}, caller={}, timestamp={}, ipfs={}",
        status, plate, caller, timestamp, ipfs_hash
    ));
}

// Generate Candid interface
ic_cdk::export_candid!();