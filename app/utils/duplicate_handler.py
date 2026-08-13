"""
ڈپلیکیٹ entries کو سنبھالنے کی سہولیات
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DuplicateHandler:
    """ڈپلیکیٹ entries کو detect اور handle کریں"""
    
    @staticmethod
    def find_duplicates(items, key_field):
        """
        لسٹ میں ڈپلیکیٹ کو find کریں
        items: list of dicts
        key_field: field to check for duplicates
        returns: dict with duplicates and unique items
        """
        if not items or not isinstance(items, list):
            return {'duplicates': [], 'unique': [], 'stats': {}}
        
        seen = {}
        unique = []
        duplicates = []
        
        for item in items:
            if not isinstance(item, dict):
                continue
            
            key = item.get(key_field)
            if not key:
                unique.append(item)
                continue
            
            key_str = str(key)
            
            if key_str in seen:
                # ڈپلیکیٹ ملا
                duplicates.append({
                    'first': seen[key_str],
                    'duplicate': item
                })
            else:
                seen[key_str] = item
                unique.append(item)
        
        logger.info(f"Duplicates found: {len(duplicates)}, Unique: {len(unique)}")
        
        return {
            'unique': unique,
            'duplicates': duplicates,
            'stats': {
                'total': len(items),
                'unique_count': len(unique),
                'duplicate_count': len(duplicates)
            }
        }
    
    @staticmethod
    def merge_duplicates(items, key_field, merge_strategy='keep_latest'):
        """
        ڈپلیکیٹ entries کو merge کریں
        merge_strategy:
            - 'keep_first': پہلا entry رکھیں
            - 'keep_latest': نیا entry رکھیں
            - 'merge_data': دونوں سے data شامل کریں
        """
        if not items or not isinstance(items, list):
            return []
        
        seen = {}
        merged_count = 0
        
        for item in items:
            if not isinstance(item, dict):
                continue
            
            key = item.get(key_field)
            if not key:
                continue
            
            key_str = str(key)
            
            if key_str not in seen:
                seen[key_str] = item
            else:
                # ڈپلیکیٹ سے deal کریں
                if merge_strategy == 'keep_first':
                    pass  # موجودہ رکھیں
                
                elif merge_strategy == 'keep_latest':
                    # تاریخ یا updated_at سے check کریں
                    old_item = seen[key_str]
                    old_time = old_item.get('updated_at') or old_item.get('date') or old_item.get('timestamp') or ''
                    new_time = item.get('updated_at') or item.get('date') or item.get('timestamp') or ''
                    
                    if str(new_time) > str(old_time):
                        seen[key_str] = item
                        merged_count += 1
                
                elif merge_strategy == 'merge_data':
                    # دونوں سے data شامل کریں
                    merged = DuplicateHandler._merge_dicts(seen[key_str], item)
                    seen[key_str] = merged
                    merged_count += 1
        
        result = list(seen.values())
        logger.info(f"Merged {merged_count} duplicates. Result: {len(result)} items")
        return result
    
    @staticmethod
    def _merge_dicts(dict1, dict2):
        """دو dicts کو محفوظ طریقے سے merge کریں"""
        merged = dict1.copy()
        
        for key, value in dict2.items():
            if key not in merged or merged[key] is None:
                merged[key] = value
            elif isinstance(value, list):
                # لسٹوں کو شامل کریں
                if isinstance(merged[key], list):
                    merged[key] = list(set(merged[key] + value))
            elif isinstance(value, dict):
                # Dicts کو recursively merge کریں
                if isinstance(merged[key], dict):
                    merged[key] = DuplicateHandler._merge_dicts(merged[key], value)
        
        return merged
    
    @staticmethod
    def detect_similar_entries(items, key_field, similarity_threshold=0.8):
        """
        ملتے جلتے entries کو detect کریں (not exact duplicates)
        similarity_threshold: 0.0 - 1.0
        """
        if not items or len(items) < 2:
            return []
        
        from difflib import SequenceMatcher
        
        similar_groups = []
        checked = set()
        
        for i, item1 in enumerate(items):
            if i in checked:
                continue
            
            key1 = str(item1.get(key_field, ''))
            similar_group = [i]
            
            for j, item2 in enumerate(items[i+1:], i+1):
                if j in checked:
                    continue
                
                key2 = str(item2.get(key_field, ''))
                
                # String similarity چیک کریں
                ratio = SequenceMatcher(None, key1, key2).ratio()
                
                if ratio >= similarity_threshold:
                    similar_group.append(j)
                    checked.add(j)
            
            if len(similar_group) > 1:
                similar_groups.append(similar_group)
                checked.add(i)
        
        logger.info(f"Similar entries found: {len(similar_groups)} groups")
        return similar_groups
    
    @staticmethod
    def update_or_insert(collection, key_field, item):
        """
        موجودہ item کو update کریں یا نیا شامل کریں
        """
        if not item or not isinstance(item, dict):
            return False
        
        key = item.get(key_field)
        if not key:
            logger.warning("Key field missing from item")
            return False
        
        # یہاں logic depends on data structure
        # SQL سے لیے:
        # UPDATE items SET ... WHERE key_field = ? ELSE INSERT
        # In-memory list کے لیے:
        
        found = False
        for i, existing in enumerate(collection):
            if existing.get(key_field) == key:
                # Update موجودہ
                collection[i] = item
                found = True
                break
        
        if not found:
            # Insert نیا
            collection.append(item)
        
        return True
    
    @staticmethod
    def batch_upsert(collection, key_field, items, log_stats=True):
        """
        متعدد items کو batch میں update/insert کریں
        """
        if not items:
            return {'inserted': 0, 'updated': 0, 'failed': 0}
        
        inserted = 0
        updated = 0
        failed = 0
        
        for item in items:
            try:
                key = item.get(key_field)
                if not key:
                    failed += 1
                    continue
                
                found = False
                for existing in collection:
                    if existing.get(key_field) == key:
                        existing.update(item)
                        updated += 1
                        found = True
                        break
                
                if not found:
                    collection.append(item)
                    inserted += 1
            
            except Exception as e:
                logger.error(f"Upsert failed for item {item.get(key_field)}: {e}")
                failed += 1
        
        if log_stats:
            logger.info(f"Batch upsert: {inserted} inserted, {updated} updated, {failed} failed")
        
        return {
            'inserted': inserted,
            'updated': updated,
            'failed': failed
        }

