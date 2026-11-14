import { UsersService } from './users.service';

export class UsersController {
    constructor(private readonly usersService: UsersService) {}

    getUsers(): string[] {
        return this.usersService.findAll();
    }
}
