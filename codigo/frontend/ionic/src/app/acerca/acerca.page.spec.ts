import { ComponentFixture, TestBed } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';
import { RouterTestingModule } from '@angular/router/testing';

import { AcercaPage } from './acerca.page';
import { SharedModule } from '../shared/shared.module';

describe('AcercaPage', () => {
  let component: AcercaPage;
  let fixture: ComponentFixture<AcercaPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [AcercaPage],
      imports: [IonicModule.forRoot(), RouterTestingModule, SharedModule],
    }).compileComponents();

    fixture = TestBed.createComponent(AcercaPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
