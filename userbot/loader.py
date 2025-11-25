"""
Module loader for the userbot.
Automatically discovers and loads all modules from the modules directory.
Provides a clean interface for registering command handlers.
"""

import os
import sys
import importlib
import importlib.util
from typing import Dict, List, Callable, Any, Optional
from telethon import TelegramClient, events

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config


class ModuleInfo:
    """Stores information about a loaded module."""
    
    def __init__(self, name: str, description: str = "", commands: List[str] = None):
        self.name = name
        self.description = description
        self.commands = commands or []
        self.handlers: List[Any] = []


class ModuleLoader:
    """
    Handles dynamic loading of userbot modules.
    Discovers modules in the modules directory and registers their handlers.
    """
    
    def __init__(self, client: TelegramClient, owner_id: int = None):
        """
        Initialize the module loader.
        
        Args:
            client: The Telethon client to register handlers with
            owner_id: The user ID who owns this userbot instance
        """
        self.client = client
        self.owner_id = owner_id  # This user's ID
        self.modules: Dict[str, ModuleInfo] = {}
        self.modules_path = os.path.join(os.path.dirname(__file__), "modules")
        
    def load_all_modules(self) -> int:
        """
        Load all modules from the modules directory.
        
        Returns:
            Number of modules successfully loaded
        """
        if not os.path.exists(self.modules_path):
            os.makedirs(self.modules_path)
            return 0
        
        loaded_count = 0
        
        # Get all Python files in modules directory
        for filename in os.listdir(self.modules_path):
            if filename.endswith(".py") and not filename.startswith("_"):
                module_name = filename[:-3]  # Remove .py extension
                
                try:
                    if self.load_module(module_name):
                        loaded_count += 1
                except Exception as e:
                    print(f"⚠️ Failed to load module '{module_name}': {e}")
        
        return loaded_count
    
    def load_module(self, module_name: str) -> bool:
        """
        Load a specific module by name.
        
        Args:
            module_name: Name of the module to load (without .py extension)
            
        Returns:
            True if loaded successfully, False otherwise
        """
        module_path = os.path.join(self.modules_path, f"{module_name}.py")
        
        if not os.path.exists(module_path):
            return False
        
        # Load the module
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            return False
            
        module = importlib.util.module_from_spec(spec)
        sys.modules[f"userbot.modules.{module_name}"] = module
        spec.loader.exec_module(module)
        
        # Check if module has setup function
        if hasattr(module, "setup"):
            # Call setup with client and loader
            module_info = module.setup(self.client, self)
            
            if isinstance(module_info, ModuleInfo):
                self.modules[module_name] = module_info
                return True
        
        # If no setup function, just register the module
        self.modules[module_name] = ModuleInfo(
            name=module_name,
            description=getattr(module, "__doc__", "No description")
        )
        
        return True
    
    def register_handler(self, handler: Any, module_info: ModuleInfo):
        """
        Register an event handler and associate it with a module.
        
        Args:
            handler: The event handler to register
            module_info: The module info to associate with
        """
        self.client.add_event_handler(handler)
        module_info.handlers.append(handler)
    
    def get_all_modules(self) -> Dict[str, ModuleInfo]:
        """
        Get all loaded modules.
        
        Returns:
            Dictionary of module name to ModuleInfo
        """
        return self.modules
    
    def get_module(self, name: str) -> Optional[ModuleInfo]:
        """
        Get a specific module by name.
        
        Args:
            name: Module name
            
        Returns:
            ModuleInfo or None if not found
        """
        return self.modules.get(name)


def owner_only(func: Callable) -> Callable:
    """
    Decorator to restrict command to owner only.
    Silently ignores commands from non-owners.
    
    Args:
        func: The handler function to wrap
        
    Returns:
        Wrapped function that checks owner
    """
    async def wrapper(event):
        # Check if sender is the owner
        sender_id = event.sender_id
        if sender_id != config.OWNER_ID:
            return  # Silently ignore
        
        return await func(event)
    
    return wrapper


def auto_delete(func: Callable) -> Callable:
    """
    Decorator to auto-delete the command message after execution.
    
    Args:
        func: The handler function to wrap
        
    Returns:
        Wrapped function that deletes the command message
    """
    async def wrapper(event):
        try:
            # Execute the handler
            result = await func(event)
            
            # Delete the command message
            try:
                await event.delete()
            except Exception:
                pass  # Silently fail if can't delete
            
            return result
        except Exception as e:
            # Still try to delete on error
            try:
                await event.delete()
            except Exception:
                pass
            raise e
    
    return wrapper


def command(pattern: str, owner: bool = True, delete: bool = True):
    """
    Decorator factory for creating command handlers.
    
    Args:
        pattern: Regex pattern for the command (without prefix)
        owner: Whether to restrict to owner only (default True)
        delete: Whether to auto-delete the command message (default True)
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        # Build the full pattern with prefix
        full_pattern = f"^\\{config.CMD_PREFIX}{pattern}"
        
        # Apply decorators in order
        handler = func
        if delete:
            handler = auto_delete(handler)
        if owner:
            handler = owner_only(handler)
        
        # Store the pattern for reference
        handler._pattern = full_pattern
        handler._command = pattern.split("(")[0].split("\\")[0]  # Extract base command
        
        return handler
    
    return decorator
